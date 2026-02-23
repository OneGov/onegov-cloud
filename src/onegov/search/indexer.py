from __future__ import annotations

import re

from itertools import groupby
from onegov.core.utils import is_non_string_iterable
from onegov.search import index_log, log, Searchable, utils
from onegov.search.datamanager import IndexerDataManager
from onegov.search.search_index import SearchIndex
from onegov.search.utils import language_from_locale
from operator import itemgetter
from sqlalchemy import and_, bindparam, delete, func, text, String
from sqlalchemy.orm import object_session
from sqlalchemy.orm.exc import ObjectDeletedError
from sqlalchemy.dialects.postgresql import insert, ARRAY
from uuid import UUID


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
    from datetime import datetime
    from sqlalchemy.orm import InstrumentedAttribute, Session
    from sqlalchemy.sql import ColumnElement
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
        title: str
        properties: dict[str, str]

    class DeleteTask(TypedDict):
        action: Literal['delete']
        id: UUID | str | int
        schema: str
        owner_type: str
        tablename: str

    Task: TypeAlias = IndexTask | DeleteTask
    PKColumn: TypeAlias = (
        InstrumentedAttribute[UUID | None]
        | InstrumentedAttribute[int | None]
        | InstrumentedAttribute[str | None]
    )


class Indexer:

    def __init__(
        self,
        mappings: TypeMappingRegistry,
        languages: set[str] | None = None
    ) -> None:
        self.mappings = mappings
        self.languages = languages or {'simple'}

    def index(
        self,
        tasks: list[IndexTask] | IndexTask,
        session: Session,
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
        # NOTE: Since we might receive multiple IndexTasks for the same
        #       row, we use a dictionary to deduplicate those tasks into
        #       the final task in this list. Performing the IndexTasks
        #       in sequence would lead to the same result anyways and
        #       this avoid ON CONFLICT triggering multiple times for the
        #       same row, which is not allowed.
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

                detected_language = task['language']
                if language_from_locale(detected_language) == 'simple':
                    detected_language = 'simple'

                if detected_language not in self.languages:
                    if len(self.languages) == 1:
                        language = next(iter(self.languages))
                    else:
                        # prioritize german and then french locales
                        for locale in ('de_CH', 'de', 'fr_CH', 'fr'):
                            if locale in self.languages:
                                language = locale
                                break
                        else:
                            # if there is nothing to prioritize, just pick one
                            language = next(iter(self.languages), 'simple')
                else:
                    language = detected_language
                _properties = task['properties']
                _tags = task['tags']

                # NOTE: We use a dictionary to avoid duplicate updates for
                #       the same model, only the latest update will count
                params_dict[_owner_id] = {
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
                    '_title_string': task['title'],
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

            title_vector: ColumnElement[str] | None = None
            for language in self.languages:
                title_vector_part = func.setweight(
                    func.to_tsvector(
                        bindparam(f'_lang__{language}', type_=String),
                        bindparam('_title_string', type_=String)
                    ),
                    'A'
                )
                if title_vector is None:
                    title_vector = title_vector_part
                else:
                    title_vector = title_vector.op('||')(title_vector_part)

            data_vector: ColumnElement[str] = func.setweight(
                func.array_to_tsvector(
                    bindparam('_tags', type_=ARRAY(String))
                ),
                'A'
            )
            for field in tasks[0]['properties'].keys():
                for language in self.languages:
                    data_vector = data_vector.op('||')(
                        func.setweight(
                            func.to_tsvector(
                                bindparam(f'_lang__{language}', type_=String),
                                bindparam(f'_{field}', type_=String)
                            ),
                            bindparam(f'_weight__{field}__{language}')
                        )
                    )

            stmt = insert(SearchIndex.__table__).values(  # type: ignore[arg-type]
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
                    SearchIndex.title_vector: title_vector,
                    SearchIndex.data_vector: data_vector,
                }
            )
            # we may have already indexed this model
            # so perform an update instead
            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    SearchIndex.owner_tablename,
                    owner_id_column
                ],
                set_={
                    # the owner_type can change, although uncommon
                    'owner_type': stmt.excluded.owner_type,
                    'publication_start': stmt.excluded.publication_start,
                    'publication_end': stmt.excluded.publication_end,
                    'public': stmt.excluded.public,
                    'access': stmt.excluded.access,
                    'last_change': stmt.excluded.last_change,
                    'tags': stmt.excluded.tags,
                    'suggestion': stmt.excluded.suggestion,
                    'title_vector': stmt.excluded.title_vector,
                    'data_vector': stmt.excluded.data_vector,
                },
                # since our unique constraints are partial indeces
                # we need this index_where clause, otherwise postgres
                # will not be able to infer the matching constraint
                index_where=owner_id_column.is_not(None)
            )
            with session.begin_nested():
                session.execute(stmt, list(params_dict.values()))
        except Exception:
            index_log.exception(
                f'Error creating index schema {schema} of '
                f'table {tablename}, tasks: {[t["id"] for t in tasks]}',
            )
            return False

        return True

    def delete(
        self,
        tasks: list[IndexTask] | IndexTask,
        session: Session
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
                delete(SearchIndex.__table__)  # type: ignore[arg-type]
                .where(and_(
                    SearchIndex.owner_tablename == tablename,
                    owner_id_column.in_(owner_ids)
                ))
            )
            with session.begin_nested():
                session.execute(stmt)
        except Exception:
            index_log.exception(
                f'Error deleting index schema {schema} tasks {tasks}:'
            )
            return False

        return True

    def process(
        self,
        tasks: Iterable[Task],
        session: Session
    ) -> int:
        """ Processes the queue in bulk.

        Gathers all tasks and groups them by action and owner type.

        Returns the number of successfully processed batches.
        """

        grouped_tasks = groupby(
            tasks,
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
                success += self.index(
                    task_list,  # type: ignore[arg-type]
                    session
                )
            elif action == 'delete':
                success += self.delete(
                    task_list,  # type: ignore[arg-type]
                    session
                )
            else:
                raise NotImplementedError(
                    f"Action '{action}' not implemented for {self.__class__}")
        return success

    def delete_search_index(self, session: Session) -> None:
        """ Immediately delete all records in search index table. """
        session.execute(text("""
            TRUNCATE search_index;
            COMMIT;
        """))


class TypeMapping:
    __slots__ = ('name', 'mapping', 'title_property', 'model')

    def __init__(
        self,
        name: str,
        mapping: dict[str, Any],
        title_property: str | None = None,
        model: type[Searchable] | None = None
    ) -> None:
        self.name = name
        self.mapping = mapping
        self.title_property = title_property
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
            self.register_type(
                model.__name__,
                model.fts_properties,
                model.fts_title_property,
                model
            )

    def register_type(
        self,
        type_name: str,
        mapping: dict[str, Any],
        title_property: str | None = None,
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
        self.mappings[type_name] = TypeMapping(
            type_name,
            mapping,
            title_property,
            model
        )

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

    def __init__(
        self,
        indexer: Indexer,
        max_queue_size: int = 0,
        languages: Sequence[str] = ('de', 'fr', 'en')
    ) -> None:
        self.indexer = indexer
        self.mappings = indexer.mappings
        self.detector = ORMLanguageDetector(languages)
        self.max_queue_size = max_queue_size
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

    def on_delete(self, schema: str, session: Session, obj: object) -> None:
        if not self.stopped:
            if isinstance(obj, Searchable):
                self.delete(schema, obj, session)

    def on_transaction_join(self, schema: str, session: Session) -> None:
        if not self.stopped:
            # NOTE: This ensures IndexerDataManager gets created before
            #       the transaction is in its `Comitting` state, where
            #       it no longer can be joined.
            IndexerDataManager.get_queue(
                session,
                self.indexer,
                self.max_queue_size
            )

    def put(self, session: Session, translation: Task) -> None:
        queue = IndexerDataManager.get_queue(
            session,
            self.indexer,
            self.max_queue_size
        )
        if queue is None:
            log.error(
                'Tried to put events into the ORM translation queue '
                'while the transaction was in an invalid state.'
            )
            return
        queue.append(translation)

    def index_task(
        self,
        schema: str,
        obj: Searchable,
    ) -> IndexTask | None:
        try:
            if obj.fts_skip:
                return None

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
                'title': '',
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
                translation['properties'][prop] = value

            if mapping_.title_property is not None:
                if (existing := translation['properties'].get(
                    mapping_.title_property
                )) is not None:
                    translation['title'] = existing
                else:
                    raw = getattr(obj, mapping_.title_property)
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
                    translation['title'] = value

            suggestion = obj.fts_suggestion
            if suggestion:
                if is_non_string_iterable(suggestion):
                    suggestion = list(suggestion)
                else:
                    suggestion = [str(suggestion)]

                translation['suggestion'] = suggestion

            return translation
        except ObjectDeletedError:
            obj_id = getattr(obj, 'id', obj)
            log.info(
                f'Object {obj_id} was deleted before indexing:',
                exc_info=True
            )
            return None

    def delete_task(self, schema: str, obj: Searchable) -> DeleteTask:
        return {
            'action': 'delete',
            'schema': schema,
            'tablename': obj.__tablename__,
            'owner_type': obj.__class__.__name__,
            'id': getattr(obj, obj.fts_id)
        }

    def index(
        self,
        schema: str,
        obj: Searchable,
        session: Session | None = None,
    ) -> None:
        """
        Creates or updates index for the given object

        """
        if session is None:
            session = object_session(obj)
            assert session is not None
        task = self.index_task(schema, obj)
        if task is not None:
            self.put(session, task)

    def delete(
        self,
        schema: str,
        obj: Searchable,
        session: Session | None = None,
    ) -> None:
        """
        Deletes index of the given object

        """
        if session is None:
            session = object_session(obj)
            assert session is not None
        self.put(session, self.delete_task(schema, obj))
