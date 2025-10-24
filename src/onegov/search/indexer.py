from __future__ import annotations

import re

from itertools import groupby
from queue import Empty, Queue, Full
from onegov.core.utils import is_non_string_iterable
from onegov.search import index_log, log, Searchable, utils
from onegov.search.search_index import SearchIndex
from onegov.search.utils import language_from_locale, normalize_text
from operator import itemgetter
from sqlalchemy import and_, bindparam, func, String, Table, MetaData
from sqlalchemy.orm.exc import ObjectDeletedError
from sqlalchemy.dialects.postgresql import insert, ARRAY
from uuid import UUID


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from datetime import datetime
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session
    from sqlalchemy.sql import ColumnElement
    from sqlalchemy.sql.expression import Executable
    from typing import TypeAlias
    from typing import TypedDict

    class IndexTask(TypedDict):
        action: Literal['index']
        id: UUID | str | int
        id_key: str
        schema: str
        tablename: str
        owner_type: str
        language: str
        access: str
        public: bool
        suggestion: list[str]
        tags: list[str]
        last_change: datetime | None
        publication_start: datetime | None
        publication_end: datetime | None
        properties: dict[str, str]

    class DeleteTask(TypedDict):
        action: Literal['delete']
        id: UUID | str | int
        schema: str
        owner_type: str
        tablename: str

    Task: TypeAlias = IndexTask | DeleteTask
    PKColumn: TypeAlias = (
        ColumnElement[UUID | None]
        | ColumnElement[int | None]
        | ColumnElement[str | None]
    )


class Indexer:
    queue: Queue[Task]

    def __init__(
        self,
        mappings: TypeMappingRegistry,
        queue: Queue[Task],
        engine: Engine,
        languages: set[str] | None = None
    ) -> None:
        self.mappings = mappings
        self.queue = queue
        self.engine = engine
        self.languages = languages or {'simple'}

    def index(
        self,
        tasks: list[IndexTask] | IndexTask,
        session: Session | None = None,
    ) -> bool:
        """ Update the 'search_index' table (full text search index) of
        the given object(s)/task(s).

        In case of a bunch of tasks we are assuming they are all from the
        same schema and table in order to optimize the indexing process.

        When a session is passed we use that session's transaction context
        and use a savepoint instead of our own transaction to perform the
        action.

        :param tasks: A list of tasks to index
        :param session: Supply an active session
        :return: True if the indexing was successful, False otherwise

        """
        params_dict = {}

        if not isinstance(tasks, list):
            tasks = [tasks]

        if not tasks:
            # nothing to do
            return True

        tablename: str | None = None
        schema: str | None = None
        owner_id_column: PKColumn | None = None
        try:
            for task in tasks:
                if schema is not None:
                    if schema != task['schema']:
                        index_log.error(
                            'Received mixed schemas in search delete tasks.'
                        )
                        return False
                else:
                    schema = task['schema']

                if tablename is not None:
                    if tablename != task['tablename']:
                        index_log.error(
                            'Received mixed tables in search delete tasks.'
                        )
                        return False
                else:
                    tablename = task['tablename']

                _owner_type = task['owner_type']  # class name
                _mapping = self.mappings[_owner_type]
                _owner_id = task['id']
                _owner_id_column: PKColumn
                if isinstance(_owner_id, UUID):
                    _owner_id_column = SearchIndex.owner_id_uuid
                elif isinstance(_owner_id, int):
                    _owner_id_column = SearchIndex.owner_id_int
                elif isinstance(_owner_id, str):
                    _owner_id_column = SearchIndex.owner_id_str

                if owner_id_column is not None:
                    if owner_id_column is not _owner_id_column:
                        index_log.error(
                            'Received mixed id types in search delete tasks.'
                        )
                        return False
                else:
                    owner_id_column = _owner_id_column

                detected_language = language_from_locale(task['language'])
                if detected_language not in self.languages:
                    if len(self.languages) == 1:
                        language = next(iter(self.languages))
                    elif 'german' in self.languages:
                        language = 'german'
                    elif 'french' in self.languages:
                        language = 'french'
                    else:
                        # HACK: just take one
                        language = next(iter(self.languages), 'simple')
                else:
                    language = detected_language
                _properties = task['properties']
                _tags = task['tags']

                # NOTE: We use a dictionary to avoid duplicate updates for
                #       the same model, only the latest update will count
                params_dict[_owner_id] = {
                    '_data': _properties,
                    '_owner_id': _owner_id,
                    '_owner_type': _owner_type,
                    '_owner_tablename': tablename,
                    '_public': task['public'],
                    '_access': task.get('access', 'public'),
                    '_last_change': task['last_change'],
                    '_tags': _tags,
                    '_suggestion': task['suggestion'],
                    '_publication_start':
                        task.get('publication_start', None),
                    '_publication_end':
                        task.get('publication_end', None),
                    **{
                        f'_lang__{lang}': lang
                        for lang in self.languages
                    },
                    **{
                        f'_{k}': v
                        for k, v in _properties.items()
                    }
                }
                for field in _properties.keys():
                    _config = _mapping.mapping.get(field, {})
                    _weight = _config.get('weight')
                    if _weight not in ('A', 'B', 'C', 'D'):
                        index_log.warn(
                            f'Invalid weight for property "{field}" on type '
                            f'"{_owner_type}", falling back to weight "C".'
                        )
                        _weight = 'C'
                    for lang in self.languages:
                        params_dict[_owner_id][
                            f'_weight__{field}__{lang}'
                        ] = chr(ord(_weight) + 1) if (
                            'localized' in _config.get('type', '')
                            and lang != language
                            # TODO: Do we want to emit a warning if we can't
                            #       de-prioritize non-matching languages?
                            and _weight != 'D'
                        ) else _weight

            assert schema is not None
            assert owner_id_column is not None
            combined_vector = func.setweight(
                func.array_to_tsvector(
                    bindparam('_tags', type_=ARRAY(String))
                ),
                'A'
            )
            for field in tasks[0]['properties'].keys():
                for language in self.languages:
                    combined_vector = combined_vector.op('||')(
                        func.setweight(
                            func.to_tsvector(
                                bindparam(f'_lang__{language}', type_=String),
                                bindparam(f'_{field}', type_=String)
                            ),
                            bindparam(f'_weight__{field}__{language}')
                        )
                    )

            stmt = (
                insert(SearchIndex.__table__)
                .values(
                    {
                        owner_id_column: bindparam('_owner_id'),
                        SearchIndex.owner_type: bindparam('_owner_type'),
                        SearchIndex.owner_tablename:
                            bindparam('_owner_tablename'),
                        SearchIndex.publication_start:
                            bindparam('_publication_start'),
                        SearchIndex.publication_end:
                            bindparam('_publication_end'),
                        SearchIndex.public: bindparam('_public'),
                        SearchIndex.access: bindparam('_access'),
                        SearchIndex.last_change: bindparam('_last_change'),
                        SearchIndex._tags:
                            bindparam('_tags', type_=ARRAY(String)),
                        SearchIndex.suggestion: bindparam('_suggestion'),
                        SearchIndex.fts_idx_data: bindparam('_data'),
                        SearchIndex.fts_idx: combined_vector,
                    }
                )
                # we may have already indexed this model
                # so perform an update instead
                .on_conflict_do_update(
                    index_elements=[
                        SearchIndex.owner_tablename,
                        owner_id_column
                    ],
                    set_={
                        # the owner_type can change, although uncommon
                        'owner_type': bindparam('_owner_type'),
                        'publication_start': bindparam('_publication_start'),
                        'publication_end': bindparam('_publication_end'),
                        'public': bindparam('_public'),
                        'access': bindparam('_access'),
                        'last_change': bindparam('_last_change'),
                        'tags': bindparam('_tags', type_=ARRAY(String)),
                        'suggestion': bindparam('_suggestion'),
                        'fts_idx_data': bindparam('_data'),
                        'fts_idx': combined_vector,
                    },
                    # since our unique constraints are partial indeces
                    # we need this index_where clause, otherwise postgres
                    # will not be able to infer the matching constraint
                    index_where=owner_id_column.isnot(None)  # type: ignore[no-untyped-call]
                )
            )
            params = list(params_dict.values())

            self.execute_statement(session, schema, stmt, params)
        except Exception:
            index_log.exception(
                f'Error creating index schema {schema} of '
                f'table {tablename}, tasks: {[t["id"] for t in tasks]}',
            )
            return False

        return True

    def execute_statement(
        self,
        session: Session | None,
        schema: str,
        stmt: Executable,
        params: list[dict[str, Any]] | None = None
    ) -> None:

        if session is None:
            with self.engine.connect() as connection:
                connection = connection.execution_options(
                    schema_translate_map={None: schema}
                )
                with connection.begin():
                    connection.execute(stmt, params or [{}])
        else:
            # use a savepoint instead
            with session.begin_nested():
                session.execute(stmt, params or [{}])

    def delete(
        self,
        tasks: list[IndexTask] | IndexTask,
        session: Session | None = None
    ) -> bool:

        if not isinstance(tasks, list):
            tasks = [tasks]

        schema: str | None = None
        tablename: str | None = None
        owner_ids: set[UUID | int | str] = set()
        owner_id_column: PKColumn | None = None
        for task in tasks:
            if schema is not None:
                if schema != task['schema']:
                    index_log.error(
                        'Received mixed schemas in search delete tasks.'
                    )
                    return False
            else:
                schema = task['schema']

            if tablename is not None:
                if tablename != task['tablename']:
                    index_log.error(
                        'Received mixed tables in search delete tasks.'
                    )
                    return False
            else:
                tablename = task['tablename']

            _owner_id = task['id']
            _owner_id_column: PKColumn
            owner_ids.add(_owner_id)
            if isinstance(_owner_id, UUID):
                _owner_id_column = SearchIndex.owner_id_uuid
            elif isinstance(_owner_id, int):
                _owner_id_column = SearchIndex.owner_id_int
            elif isinstance(_owner_id, str):
                _owner_id_column = SearchIndex.owner_id_str

            if owner_id_column is not None:
                if owner_id_column is not _owner_id_column:
                    index_log.error(
                        'Received mixed id types in search delete tasks.'
                    )
                    return False
            else:
                owner_id_column = _owner_id_column

        if not owner_ids:
            # nothing to delete
            return True

        try:
            assert schema is not None
            assert tablename is not None
            assert owner_id_column is not None
            stmt = (
                SearchIndex.__table__.delete()
                .where(and_(
                    SearchIndex.owner_tablename == tablename,
                    owner_id_column.in_(owner_ids)
                ))
            )
            self.execute_statement(session, schema, stmt)
        except Exception:
            index_log.exception(
                f'Error deleting index schema {schema} tasks {tasks}:'
            )
            return False

        return True

    # FIXME: We should consider making the session parameter mandatory
    def process(self, session: Session | None = None) -> int:
        """ Processes the queue in bulk.

        Gathers all tasks and groups them by action and owner type.

        Returns the number of successfully processed batches.
        """

        def task_generator() -> Iterator[Task]:
            while True:
                try:
                    task = self.queue.get(block=False, timeout=None)
                except Empty:
                    break
                else:
                    self.queue.task_done()
                    yield task

        grouped_tasks = groupby(
            task_generator(),
            # NOTE: We could group by tablename for delete actions
            #       which could yield slightly larger batches in
            #       some cases, but for indexing we currently
            #       can't do that, because properties may differ
            #       between multiple polymorphic variants
            key=itemgetter('schema', 'action', 'owner_type')
        )
        success = 0
        for (_, action, _), tasks in grouped_tasks:
            task_list = list(tasks)

            if action == 'index':
                success += self.index(task_list, session)  # type: ignore[arg-type]
            elif action == 'delete':
                success += self.delete(task_list, session)  # type: ignore[arg-type]
            else:
                raise NotImplementedError(
                    f"Action '{action}' not implemented for {self.__class__}")
        return success

    def delete_search_index(self, schema: str) -> None:
        """ Delete all records in search index table of the given `schema`. """

        metadata = MetaData(schema=schema)
        search_index_table = Table(SearchIndex.__tablename__, metadata)
        stmt = search_index_table.delete()

        connection = self.engine.connect()
        with connection.begin():
            connection.execute(stmt)


class TypeMapping:
    __slots__ = ('name', 'mapping', 'model')

    def __init__(
        self,
        name: str,
        mapping: dict[str, Any],
        model: type[Searchable] | None = None
    ) -> None:
        self.name = name
        self.mapping = mapping
        self.model = model


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
            self.register_type(model.__name__, model.fts_properties, model)

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
        assert type_name not in self.mappings, (
            f"Type '{type_name}' already registered")
        self.mappings[type_name] = TypeMapping(type_name, mapping, model)

    @property
    def registered_fields(self) -> set[str]:
        """ Goes through all the registered types and returns the a set with
        all fields used by the mappings.

        """
        return {key for mapping in self for key in mapping.mapping.keys()}


class ORMLanguageDetector(utils.LanguageDetector):
    html_strip_expression = re.compile(r'<[^<]+?>')

    def localized_properties(self, obj: Searchable) -> Iterator[str]:
        for key, definition in obj.fts_properties.items():
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

    queue: Queue[Task]

    def __init__(
        self,
        mappings: TypeMappingRegistry,
        max_queue_size: int = 0,
        languages: Sequence[str] = ('de', 'fr', 'en')
    ) -> None:
        self.mappings = mappings
        self.queue = Queue(maxsize=max_queue_size)
        self.detector = ORMLanguageDetector(languages)
        self.stopped = False

    def on_insert(self, schema: str, obj: object) -> None:
        if not self.stopped:
            if isinstance(obj, Searchable):
                self.index(schema, obj)

    def on_update(self, schema: str, obj: object) -> None:
        if not self.stopped:
            if isinstance(obj, Searchable):
                if obj.fts_skip:
                    # NOTE: We need to emit a delete in case this
                    #       model previously wasn't skipped
                    self.delete(schema, obj)
                else:
                    self.index(schema, obj)

    def on_delete(self, schema: str, obj: object) -> None:
        if not self.stopped:
            if isinstance(obj, Searchable):
                self.delete(schema, obj)

    def put(self, translation: Task) -> None:
        try:
            self.queue.put_nowait(translation)
        except Full:
            log.error('The orm event translator queue is full!')

    def index(
        self,
        schema: str,
        obj: Searchable,
    ) -> None:
        """
        Creates or updates index for the given object

        """
        try:
            if obj.fts_skip:
                return

            if obj.fts_language == 'auto':
                language = self.detector.detect_object_language(obj)
            else:
                language = obj.fts_language

            _owner_type = obj.__class__.__name__
            translation: IndexTask = {
                'action': 'index',
                'id': getattr(obj, obj.fts_id),
                'id_key': obj.fts_id,
                'schema': schema,
                'tablename': obj.__tablename__,
                'owner_type': _owner_type,
                'language': language,
                'access': obj.fts_access,
                'public': obj.fts_public,
                'suggestion': [],
                'tags': obj.fts_tags or [],
                'last_change': obj.fts_last_change,
                'publication_start': obj.fts_publication_start,
                'publication_end': obj.fts_publication_end,
                'properties': {},
            }

            mapping_ = self.mappings[_owner_type]

            for prop in mapping_.mapping.keys():
                # FIXME: If we treat lists and dictionaries as documents
                #        then we may create some unintended combinations
                #        that are ranked highly because there are no stop
                #        words separating them. We could try to switch to
                #        `JSONB` input for `to_tsvector` which inserts at
                #        least one stop word between every value, but we
                #        might want more than one stop word of separation.
                raw = getattr(obj, prop)
                if raw is None:
                    value = ''
                elif isinstance(raw, dict):
                    # FIXME: Do we want to unnest nested structures?
                    value = ' '.join(
                        str(value)
                        for value in raw.values()
                        if value is not None
                    )
                elif is_non_string_iterable(raw):
                    # FIXME: Do we want to unnest nested structures?
                    value = ' '.join(
                        str(value)
                        for value in raw
                        if value is not None
                    )
                else:
                    value = str(raw)
                translation['properties'][prop] = normalize_text(value)

            suggestion = obj.fts_suggestion
            if suggestion:
                if is_non_string_iterable(suggestion):
                    suggestion = list(suggestion)
                else:
                    suggestion = [str(suggestion)]

                translation['suggestion'] = suggestion

            self.put(translation)
        except ObjectDeletedError:
            obj_id = getattr(obj, 'id', obj)
            log.info(
                f'Object {obj_id} was deleted before indexing:',
                exc_info=True
            )

    def delete(self, schema: str, obj: Searchable) -> None:
        """
        Deletes index of the given object

        """
        translation: DeleteTask = {
            'action': 'delete',
            'schema': schema,
            'tablename': obj.__tablename__,
            'owner_type': obj.__class__.__name__,
            'id': getattr(obj, obj.fts_id)
        }

        self.put(translation)
