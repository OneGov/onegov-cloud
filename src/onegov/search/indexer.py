from __future__ import annotations

import platform
import re
from uuid import UUID

import sqlalchemy

from copy import deepcopy

from collections.abc import Iterable
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import streaming_bulk
from itertools import groupby, chain, repeat
from queue import Queue, Empty, Full
from operator import itemgetter
from sqlalchemy import func, Table, delete, MetaData
from sqlalchemy.sql import Delete
from unidecode import unidecode

from sqlalchemy.orm.exc import ObjectDeletedError

from onegov.core.utils import hash_dictionary, is_non_string_iterable
from onegov.search import index_log, log, Searchable, utils
from onegov.search.errors import SearchOfflineError
from onegov.search.search_index import SearchIndex

from typing import Any, Literal, NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from datetime import datetime
    from elasticsearch import Elasticsearch
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session
    from typing import TypeAlias
    from typing import TypedDict

    class IndexTask(TypedDict):
        action: Literal['index']
        id: UUID | str | int
        id_key: str
        schema: str
        type_name: str  # FIXME: not needed for fts
        tablename: str
        owner_type: str
        owner_id: UUID | str | int
        language: str
        access: str
        suggestion: str | list[str]
        publication_start: datetime | None
        publication_end: datetime | None
        properties: dict[str, Any]

    class DeleteTask(TypedDict):  # FIXME: not needed for fts
        action: Literal['delete']
        id: UUID | str | int
        schema: str
        type_name: str
        tablename: str

    Task: TypeAlias = IndexTask | DeleteTask

ES_ANALYZER_MAP = {
    'en': 'english',
    'de': 'german',
    'fr': 'french',
    'en_html': 'english_html',
    'de_html': 'german_html',
    'fr_html': 'french_html',
}

ANALYSIS_CONFIG = {
    'filter': {
        'english_stop': {
            'type': 'stop',
            'stopwords': '_english_'
        },
        'english_stemmer': {
            'type': 'stemmer',
            'language': 'english'
        },
        'english_possessive_stemmer': {
            'type': 'stemmer',
            'language': 'possessive_english'
        },
        'german_stop': {
            'type': 'stop',
            'stopwords': '_german_'
        },
        'german_stemmer': {
            'type': 'stemmer',
            'language': 'light_german'
        },
        'french_elision': {
            'type': 'elision',
            'articles_case': True,
            'articles': [
                'l', 'm', 't', 'qu', 'n', 's',
                'j', 'd', 'c', 'jusqu', 'quoiqu',
                'lorsqu', 'puisqu'
            ]
        },
        'french_stop': {
            'type': 'stop',
            'stopwords': '_french_'
        },
        'french_keywords': {
            'type': 'keyword_marker',
            'keywords': ['Exemple']
        },
        'french_stemmer': {
            'type': 'stemmer',
            'language': 'light_french'
        }
    },
    'analyzer': {
        'english_html': {
            'tokenizer': 'standard',
            'char_filter': [
                'html_strip'
            ],
            'filter': [
                'english_possessive_stemmer',
                'lowercase',
                'english_stop',
                'english_stemmer'
            ]
        },
        'german_html': {
            'tokenizer': 'standard',
            'char_filter': [
                'html_strip'
            ],
            'filter': [
                'lowercase',
                'german_stop',
                'german_normalization',
                'german_stemmer'
            ]
        },
        'french_html': {
            'tokenizer': 'standard',
            'char_filter': [
                'html_strip'
            ],
            'filter': [
                'french_elision',
                'lowercase',
                'french_stop',
                'french_keywords',
                'french_stemmer'
            ]
        },
        'autocomplete': {
            'type': 'custom',
            'char_filter': ['html_strip'],
            'tokenizer': 'standard',
            'filter': ['lowercase']
        },
        'tags': {
            'type': 'custom',
            'tokenizer': 'keyword',
            'filter': ['lowercase']
        },
    }
}


class IndexParts(NamedTuple):
    hostname: str | None
    schema: str | None
    language: str | None
    type_name: str | None
    version: str | None


def parse_index_name(index_name: str) -> IndexParts:
    """ Takes the given index name and returns the hostname, schema,
    language and type_name in a dictionary.

    * If the index_name doesn't match the pattern, all values are None.
    * If the index_name has no version, the version is None.

    """
    parts = index_name.split('-')
    if len(parts) == 4:
        hostname, schema, language, type_name = parts
        version = None
    elif len(parts) == 5:
        hostname, schema, language, type_name, version = parts
    else:
        hostname = None
        schema = None
        language = None
        type_name = None
        version = None

    return IndexParts(
        hostname=hostname,
        schema=schema,
        language=language,
        type_name=type_name,
        version=version
    )


class IndexerBase:

    queue: Queue[Any]
    failed_task: Task | None = None

    def process(
        self,
        block: bool = False,
        timeout: float | None = None
    ) -> int:
        """ Processes the queue until it is empty or until there's an error.

        If there's an error, the next call to this function will try to
        execute the failed task again. This is mainly meant for elasticsearch
        outages.

        :block:
            If True, the process waits for the queue to be available. Useful
            if you run this in a separate thread.

        :timeout:
            How long the blocking call should block. Has no effect if
            ``block`` is False.

        :return: The number of successfully processed items

        """
        try:
            processed = 0
            while True:

                # get the previously failed task or a new one
                task = self.failed_task or self.queue.get(block, timeout)
                self.failed_task = None

                if self.process_task(task):
                    processed += 1
                else:
                    # if the task failed, keep it for the next run and give up
                    self.failed_task = task
                    return processed

        except Empty:
            pass

        return processed

    def process_task(self, task: Task) -> bool:
        try:
            getattr(self, task['action'])(task)
        except SearchOfflineError:
            return False

        self.queue.task_done()
        return True


class Indexer(IndexerBase):
    """ Takes actions from a queue and executes them on the elasticsearch
    cluster. Depends on :class:`IndexManager` for index management and expects
    to have the same :class:`TypeRegistry` as :class:`ORMEventTranslator`.

    The idea is that this class does the indexing/deindexing, the index manager
    sets up the indices and the orm event translator listens for changes in
    the ORM.

    A queue is used so the indexer can be run in a separate thread.

    """

    queue: Queue[Task]

    def __init__(
        self,
        mappings: TypeMappingRegistry,
        queue: Queue[Task],
        es_client: Elasticsearch,
        hostname: str | None = None
    ) -> None:
        self.es_client = es_client
        self.queue = queue
        self.hostname = hostname or platform.node()
        self.ixmgr = IndexManager(self.hostname, es_client=self.es_client)
        self.mappings = mappings

    def bulk_process(self) -> None:
        """ Processes the queue in bulk. This offers better performance but it
        is less safe at the moment and should only be used as part of
        reindexing.

        """

        def actions() -> Iterator[dict[str, Any]]:
            try:
                task = self.queue.get(block=False, timeout=None)

                if task['action'] == 'index':
                    yield {
                        '_op_type': 'index',
                        '_index': self.ensure_index(task),
                        '_id': task['id'],
                        'doc': task['properties']
                    }
                else:
                    raise NotImplementedError

            except Empty:
                pass

        for success, info in streaming_bulk(self.es_client, actions()):
            if success:
                self.queue.task_done()

    def ensure_index(self, task: IndexTask) -> str:
        return self.ixmgr.ensure_index(
            task['schema'],
            task['language'],
            self.mappings[task['type_name']],
            return_index='internal'
        )

    def index(self, task: IndexTask) -> None:
        index = self.ensure_index(task)

        self.es_client.index(
            index=index,
            id=task['id'],  # type:ignore[arg-type]
            document=task['properties']
        )

    def delete(self, task: DeleteTask) -> None:
        # get all the types this model could be stored in (with polymorphic)
        # identites, this could be many
        mapping = self.mappings[task['type_name']]

        if mapping.model:
            types = utils.related_types(mapping.model)
        else:
            types = {mapping.name}

        # delete the document from all languages (because we don't know
        # which one anymore) - and delete from all related types (polymorphic)
        for type in types:
            ix = self.ixmgr.get_external_index_name(
                schema=task['schema'],
                language='*',
                type_name=type
            )

            # for the delete operation we need the internal index names
            for internal in self.es_client.indices.get_alias(index=ix).keys():
                try:
                    self.es_client.delete(
                        index=internal,
                        id=task['id']  # type:ignore[arg-type]
                    )
                except NotFoundError:
                    pass

    def update(self, task: IndexTask) -> None:
        self.index(task)


class PostgresIndexer(IndexerBase):

    idx_language_mapping = {
        'de': 'german',
        'fr': 'french',
        'it': 'italian',
        'en': 'english',
    }

    queue: Queue[IndexTask]

    def __init__(
        self,
        queue: Queue[IndexTask],
        engine: Engine,
    ) -> None:
        self.queue = queue
        self.engine = engine

    def index(
        self,
        tasks: list[IndexTask] | IndexTask,
        session: Session | None = None,
    ) -> bool:
        """ Update the 'fts_idx' column (full text search index) of the given
        object(s)/task(s).

        In case of a bunch of tasks we are assuming they are all from the
        same schema and table in order to optimize the indexing process.

        When a session is passed we use that session's transaction context
        and use a savepoint instead of our own transaction to perform the
        action.

        :param tasks: A list of tasks to index
        :param session: Supply an active session
        :return: True if the indexing was successful, False otherwise

        """
        params = []

        if not isinstance(tasks, list):
            tasks = [tasks]

        try:
            for task in tasks:
                language = (
                    self.idx_language_mapping.get(task['language'], 'simple'))
                data = {
                    k: unidecode(str(v)) if v else ''
                    for k, v in task['properties'].items()
                    if not k.startswith('es_')}
                _owner_id: int | UUID | str = task['owner_id']
                _tags = (
                    dict.fromkeys(task['properties'].get('es_tags') or [], ''))

                params.append({
                    '_language': language,
                    '_data': data,
                    '_owner_id_int':
                        _owner_id if isinstance(_owner_id, int) else None,
                    '_owner_id_uuid':
                        _owner_id if isinstance(_owner_id, UUID) else None,
                    '_owner_id_str':
                        _owner_id if isinstance(_owner_id, str) else None,
                    '_owner_type': task['owner_type'],  # class name
                    '_public': task['properties']['es_public'],
                    '_access': task.get('access', 'public'),
                    '_last_change': task['properties']['es_last_change'],
                    '_tags': _tags,
                    '_suggestion': task['suggestion'],
                    '_publication_start':
                        task.get('publication_start', None),
                    '_publication_end':
                        task.get('publication_end', None),
                    **{f'_{k}': v for k, v in data.items()}
                })

            weighted_vector = [
                func.setweight(
                    func.to_tsvector(
                        sqlalchemy.bindparam('_language',
                                             type_=sqlalchemy.String),
                        sqlalchemy.bindparam(f'_{field}',
                                             type_=sqlalchemy.String)
                    ),
                    weight
                )
                for field, weight in zip(
                    tasks[0]['properties'].keys(),
                    chain('A', repeat('D')))
                if not field.startswith('es_')  # TODO: rename to fts_
            ]

            combined_vector = weighted_vector[0]
            for vector in weighted_vector[1:]:
                combined_vector = combined_vector.op('||')(vector)

            schema = tasks[0]['schema']

            stmt = (
                sqlalchemy.insert(SearchIndex.__table__)
                .values(
                    {
                        SearchIndex.__table__.c.owner_id_int:
                            sqlalchemy.bindparam('_owner_id_int'),
                        SearchIndex.__table__.c.owner_id_uuid:
                            sqlalchemy.bindparam('_owner_id_uuid'),
                        SearchIndex.__table__.c.owner_id_str:
                            sqlalchemy.bindparam('_owner_id_str'),
                        SearchIndex.__table__.c.owner_type:
                            sqlalchemy.bindparam('_owner_type'),
                        SearchIndex.__table__.c.publication_start:
                            sqlalchemy.bindparam('_publication_start'),
                        SearchIndex.__table__.c.publication_end:
                            sqlalchemy.bindparam('_publication_end'),
                        SearchIndex.__table__.c.public:
                            sqlalchemy.bindparam('_public'),
                        SearchIndex.__table__.c.access:
                            sqlalchemy.bindparam('_access'),
                        SearchIndex.__table__.c.last_change:
                            sqlalchemy.bindparam('_last_change'),
                        SearchIndex.__table__.c.tags:
                            sqlalchemy.bindparam('_tags'),
                        SearchIndex.__table__.c.suggestion:
                            sqlalchemy.bindparam('_suggestion'),
                        SearchIndex.__table__.c.fts_idx_data:
                            sqlalchemy.bindparam('_data'),
                        SearchIndex.__table__.c.fts_idx: combined_vector,
                    }
                )
            )

            self.execute_statement(session, schema, stmt, params)
        except Exception as ex:
            index_log.error(
                f'Error "{ex}" creating index schema {tasks[0]["schema"]} of '
                f'type {tasks[0]["owner_type"]}, tasks:',
                [t['id'] for t in tasks],
            )
            return False

        return True

    def execute_statement(
        self,
        session: Session | None,
        schema: str,
        stmt: sqlalchemy.sql.expression.Executable,
        params: list[dict[str, Any]]
    ) -> None:

        if session is None:
            connection = self.engine.connect()
            connection = connection.execution_options(
                schema_translate_map={None: schema}
            )
            with connection.begin():
                connection.execute(stmt, params)
        else:
            # use a savepoint instead
            with session.begin_nested():
                session.execute(stmt, params)

    def update(
        self,
        tasks: list[IndexTask] | IndexTask,
        session: Session | None = None
    ) -> bool:

        return self.index(tasks, session)

    def delete(
        self,
        tasks: list[IndexTask] | IndexTask,
        session: Session | None = None
    ) -> bool:

        if not isinstance(tasks, list):
            tasks = [tasks]

        try:
            for task in tasks:
                _owner_id = task['id']
                stmt: Delete | None = None

                if isinstance(_owner_id, UUID):
                    stmt = (
                        sqlalchemy.delete(SearchIndex.__table__)
                        .where(SearchIndex.owner_id_uuid == _owner_id)
                    )
                elif isinstance(_owner_id, int):
                    stmt = (
                        sqlalchemy.delete(SearchIndex.__table__)
                        .where(SearchIndex.owner_id_int == _owner_id)
                    )
                elif isinstance(_owner_id, str):
                    stmt = (
                        sqlalchemy.delete(SearchIndex.__table__)
                        .where(SearchIndex.owner_id_str == _owner_id)
                    )

                self.execute_statement(session, tasks[0]['schema'], stmt, [{}])
        except Exception as ex:
            index_log.error(f'Error "{ex}" deleting index schema '
                            f'{tasks[0]["schema"]} tasks {tasks}')
            return False

        return True

    # FIXME: bulk_process should probably be the only function we use for
    #        the Postgres indexer, we don't have to worry about individual
    #        transactions failing as much
    def bulk_process(self, session: Session | None = None) -> None:
        """ Processes the queue in bulk. This offers better performance but it
        is less safe at the moment and should only be used as part of
        reindexing.

        Gather all index tasks, group them by model and index batch-wise
        """

        def task_generator() -> Iterator[IndexTask]:
            while not self.queue.empty():
                task = self.queue.get(block=False, timeout=None)
                self.queue.task_done()
                yield task

        grouped_tasks = groupby(
            task_generator(),
            key=itemgetter('action', 'type_name')
        )
        for (action, _), tasks in grouped_tasks:
            task_list = list(tasks)

            if action == 'index':
                self.index(task_list, session)
            elif action == 'delete':
                self.delete(task_list, session)
            else:
                raise NotImplementedError(
                    f"Action '{action}' not implemented for {self.__class__}")

    def delete_search_index(self, schema: str) -> None:
        """ Delete all records in search index table of the given `schema`. """

        metadata = MetaData(schema=schema)
        search_index_table = Table(SearchIndex.__tablename__, metadata)
        stmt = delete(search_index_table)

        connection = self.engine.connect()
        with connection.begin():
            connection.execute(stmt)


class TypeMapping:
    __slots__ = ('name', 'mapping', 'version', 'model')

    def __init__(
        self,
        name: str,
        mapping: dict[str, Any],
        model: type[Searchable] | None = None
    ) -> None:
        self.name = name
        self.mapping = self.add_defaults(mapping)
        self.version = hash_dictionary(mapping)
        self.model = model

    def add_defaults(self, mapping: dict[str, Any]) -> dict[str, Any]:
        mapping['es_public'] = {
            'type': 'boolean'
        }

        mapping['es_last_change'] = {
            'type': 'date'
        }

        mapping['es_suggestion'] = {
            'analyzer': 'autocomplete',
            'type': 'completion',
            'contexts': [
                {
                    'name': 'es_suggestion_context',
                    'type': 'category'
                }
            ]
        }

        mapping['es_tags'] = {
            'analyzer': 'tags',
            'type': 'text',
        }

        return mapping

    def for_language(self, language: str) -> dict[str, Any]:
        """ Returns the mapping for the given language. Mappings can
        be slightly different for each language. That is, the analyzer
        changes.

        Because the :class:`IndexManager` puts each language into its own
        index we do not have to worry about creating different versions
        of the same mapping here.

        """
        return self.supplement_analyzer(deepcopy(self.mapping), language)

    def supplement_analyzer(
        self,
        dictionary: dict[str, Any],
        language: str
    ) -> dict[str, Any]:
        """ Iterate through the dictionary found in the type mapping and
        replace the 'localized' type with a 'text' type that includes a
        language specific analyzer.

        """
        supplement = None

        for key, value in dictionary.items():

            if hasattr(value, 'items'):
                dictionary[key] = self.supplement_analyzer(value, language)

            elif key == 'type' and value.startswith('localized'):
                supplement = value.replace('localized', language)
                break

        if supplement:
            assert 'analyzer' not in dictionary
            dictionary[key] = 'text'
            dictionary['analyzer'] = ES_ANALYZER_MAP[supplement]

        return dictionary


class TypeMappingRegistry:

    mappings: dict[str, TypeMapping]

    def __init__(self) -> None:
        self.mappings = {}

    def __getitem__(self, key: str) -> TypeMapping:
        return self.mappings[key]

    def __iter__(self) -> Iterator[TypeMapping]:
        yield from self.mappings.values()

    def register_orm_base(self, base: type[object]) -> None:
        """ Takes the given SQLAlchemy base and registers all
        :class:`~onegov.search.mixins.Searchable` objects.

        """
        for model in utils.searchable_sqlalchemy_models(base):
            self.register_type(model.es_type_name, model.es_properties, model)

    def register_type(
        self,
        type_name: str,
        mapping: dict[str, Any],
        model: type[Searchable] | None = None
    ) -> None:
        """ Registers the given type with the given mapping. The mapping is
        as dictionary representing the part below the ``mappings/type_name``.

        See:

        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/\
        indices-create-index.html#mappings>`_

        When the mapping changes, a new index is created internally and the
        alias to this index (the external name of the index) is pointed to
        this new index.

        As a consequence, a change in the mapping requires a reindex.

        """
        assert type_name not in self.mappings, \
            f"Type '{type_name}' already registered"
        self.mappings[type_name] = TypeMapping(type_name, mapping, model)

    @property
    def registered_fields(self) -> set[str]:
        """ Goes through all the registered types and returns the a set with
        all fields used by the mappings.

        """
        return {key for mapping in self for key in mapping.mapping.keys()}


class IndexManager:
    """ Manages the creation/destruction of indices. The indices it creates
    have an internal name and an external alias. To facilitate that, versions
    are used.

    """

    created_indices: set[str]

    def __init__(self, hostname: str, es_client: Elasticsearch) -> None:
        assert hostname and es_client

        self.hostname = hostname
        self.es_client = es_client
        self.created_indices = set()

    @property
    def normalized_hostname(self) -> str:
        return utils.normalize_index_segment(
            self.hostname, allow_wildcards=False)

    def query_indices(self) -> set[str]:
        """ Queryies the elasticsearch cluster for indices belonging to this
        hostname. """

        return set(
            self.es_client.cat.indices(  # type:ignore[union-attr]
                index=f'{self.normalized_hostname}-*', h='index'
            ).splitlines()
        )

    def query_aliases(self) -> set[str]:
        """ Queryies the elasticsearch cluster for aliases belonging to this
        hostname. """

        result = set()

        infos = self.es_client.indices.get_alias(
            index='{}-*'.format(self.normalized_hostname)
        )

        for info in infos.values():
            result.update(info['aliases'])

        return result

    def ensure_index(
        self,
        schema: str,
        language: str,
        mapping: TypeMapping,
        return_index: Literal['external', 'internal'] = 'external'
    ) -> str:
        """ Takes the given database schema, language and type name and
        creates an internal index with a version number and an external
        alias without the version number.

        :schema:
            The database schema this index is based on.

        :language:
            The language in ISO 639-1 format.

        :mapping:
            The :class:`TypeMapping` mapping used in this index.

        :return_index:
            The index name to return. Either 'external' or 'internal'.

        :return:
            The (external/aliased) name of the created index.

        """
        assert schema and language and mapping
        assert len(language) == 2
        assert return_index == 'external' or return_index == 'internal'

        external = self.get_external_index_name(schema, language, mapping.name)
        internal = self.get_internal_index_name(
            schema, language, mapping.name, mapping.version)

        return_value = return_index == 'external' and external or internal

        if internal in self.created_indices:
            return return_value

        if self.es_client.indices.exists(index=internal):
            self.created_indices.add(internal)
            return return_value

        # create the index
        self.es_client.indices.create(
            index=internal,
            mappings={
                'properties': mapping.for_language(language)
            },
            settings={
                'analysis': ANALYSIS_CONFIG,
                'index': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0,
                    'refresh_interval': '5s'
                }
            }
        )

        # point the alias to the new index
        self.es_client.indices.put_alias(name=external, index=internal)

        # cache the result
        self.created_indices.add(internal)

        return return_value

    def remove_expired_indices(
        self,
        current_mappings: Iterable[TypeMapping]
    ) -> int:
        """ Removes all expired indices. An index is expired if it's version
        number is no longer known in the current mappings.

        :return: The number of indices that were deleted.

        """
        active_versions = {m.version for m in current_mappings}

        count = 0
        for index in self.query_indices():
            info = parse_index_name(index)

            if info.version and info.version not in active_versions:
                self.es_client.indices.delete(index=index)
                self.created_indices.remove(index)
                count += 1

        return count

    def get_managed_indices_wildcard(self, schema: str) -> str:
        """ Returns a wildcard index name for all indices managed. """
        return '-'.join((
            utils.normalize_index_segment(
                self.hostname, allow_wildcards=False),
            utils.normalize_index_segment(
                schema, allow_wildcards=False),
            '*'
        ))

    def get_external_index_names(
        self,
        schema: str,
        languages: Iterable[str] = '*',
        types: Iterable[str] = '*'
    ) -> str:
        """ Returns a comma separated string of external index names that
        match the given arguments. Useful to pass on to elasticsearch when
        targeting multiple indices.

        """

        return ','.join(
            self.get_external_index_name(schema, language, type_name)
            for language in languages
            for type_name in types
        )

    def get_external_index_name(
        self,
        schema: str,
        language: str,
        type_name: str
    ) -> str:
        """ Generates the external index name from the given parameters. """

        return '-'.join(
            utils.normalize_index_segment(segment, allow_wildcards=True)
            for segment in (self.hostname, schema, language, type_name)
        )

    def get_internal_index_name(
        self,
        schema: str,
        language: str,
        type_name: str,
        version: str
    ) -> str:
        """ Generates the internal index name from the given parameters. """

        return '-'.join((
            self.get_external_index_name(schema, language, type_name),
            utils.normalize_index_segment(version, allow_wildcards=False)
        ))


class ORMLanguageDetector(utils.LanguageDetector):
    html_strip_expression = re.compile(r'<[^<]+?>')

    def localized_properties(self, obj: Searchable) -> Iterator[str]:
        for key, definition in obj.es_properties.items():
            if definition.get('type', '').startswith('localized'):
                yield key

    def localized_texts(
        self,
        obj: Searchable,
        max_chars: int | None = None
    ) -> Iterator[str]:

        chars = 0
        for p in self.localized_properties(obj):
            text = getattr(obj, p, '')

            if not isinstance(text, str):
                continue

            yield text.strip()

            chars += len(text)

            if max_chars is not None and max_chars <= chars:
                break

    def detect_object_language(self, obj: Searchable) -> str:
        properties = self.localized_properties(obj)

        if not properties:
            # here, the mapping will be the same for all languages
            return self.supported_languages[0]

        text = ' '.join(self.localized_texts(obj, max_chars=1024))
        text = self.html_strip_expression.sub('', text).strip()

        if not text:
            return self.supported_languages[0]

        return self.detect(text)


class ORMEventTranslator:
    """ Handles the onegov.core orm events, translates them into indexing
    actions and puts the result into a queue for the indexer to consume.

    The queue may be limited. Once the limit is reached, new events are no
    longer processed and an error is logged.

    """

    converters: dict[str, Callable[[Any], Any]] = {
        'date': lambda dt: dt and dt.isoformat(),
    }

    es_queue: Queue[Task]
    psql_queue: Queue[IndexTask]

    def __init__(
        self,
        mappings: TypeMappingRegistry,
        max_queue_size: int = 0,
        languages: Sequence[str] = ('de', 'fr', 'en')
    ) -> None:
        self.mappings = mappings
        self.es_queue = Queue(maxsize=max_queue_size)
        self.psql_queue = Queue(maxsize=max_queue_size)
        self.detector = ORMLanguageDetector(languages)
        self.stopped = False

    def on_insert(self, schema: str, obj: object) -> None:
        if not self.stopped:
            if isinstance(obj, Searchable):
                self.index(schema, obj)

    def on_update(self, schema: str, obj: object) -> None:
        if not self.stopped:
            if isinstance(obj, Searchable):
                self.delete(schema, obj)
                self.index(schema, obj)

    def on_delete(self, schema: str, obj: object) -> None:
        if not self.stopped:
            if isinstance(obj, Searchable):
                self.delete(schema, obj)

    def put(self, translation: IndexTask) -> None:
        try:
            self.es_queue.put_nowait(translation)
            self.psql_queue.put_nowait(translation)

        except Full:
            log.error('The orm event translator queue is full!')

    def index(
        self, schema: str,
        obj: Searchable,
    ) -> None:
        """
        Creates or updates index for the given object

        """
        try:
            if obj.es_skip:
                return

            if obj.es_language == 'auto':
                language = self.detector.detect_object_language(obj)
            else:
                language = obj.es_language

            translation: IndexTask = {
                'action': 'index',
                'id': getattr(obj, obj.es_id),
                'id_key': obj.es_id,
                'schema': schema,
                'type_name': obj.es_type_name,
                # FIXME: tablename not needed for fts
                'tablename': obj.__tablename__,  # type:ignore[attr-defined]
                'owner_type': obj.__class__.__name__,
                'owner_id': getattr(obj, obj.es_id),
                'language': language,
                'access': '',
                'suggestion': '',
                'publication_start': None,
                'publication_end': None,
                'properties': {},
            }

            mapping_ = self.mappings[obj.es_type_name].for_language(language)

            for prop in mapping_.keys():
                if prop == 'es_suggestion':
                    continue

                raw = getattr(obj, prop)
                if is_non_string_iterable(raw):
                    translation['properties'][prop] = list(raw)
                else:
                    translation['properties'][prop] = raw

            for attr in ['access', 'publication_start', 'publication_end']:
                if hasattr(obj, attr):
                    translation[attr] = getattr(obj, attr)  # type:ignore[literal-required]

            # FIXME: remove once es is migrated to postgres
            if obj.es_public:
                contexts = {'es_suggestion_context': ['public']}
            else:
                contexts = {'es_suggestion_context': ['private']}

            translation['properties']['es_suggestion'] = {
                'input': obj.es_suggestion,
                'contexts': contexts
            }
            # end FIXME

            # fts suggestion
            suggestion = obj.es_suggestion
            if suggestion:
                if isinstance(suggestion, str):
                    suggestion = [s.strip() for s in suggestion.split(',')]
                elif isinstance(suggestion, Iterable):
                    suggestion = list(suggestion)

                translation['suggestion'] = suggestion

            self.put(translation)
        except ObjectDeletedError as ex:
            if hasattr(obj, 'id'):
                log.info(f'Object {obj.id} was deleted before indexing: {ex}')
            else:
                log.info(f'Object {obj} was deleted before indexing: {ex}')

    def delete(self, schema: str, obj: Searchable) -> None:
        """
        Deletes index of the given object

        """
        translation: DeleteTask = {
            'action': 'delete',
            'schema': schema,
            'type_name': obj.es_type_name,
            # FIXME: tablename not needed for fts
            'tablename': obj.__tablename__,  # type:ignore[attr-defined]
            'id': getattr(obj, obj.es_id)
        }

        self.put(translation)  # type:ignore[arg-type]
