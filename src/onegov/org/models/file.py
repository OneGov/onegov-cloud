""" Contains the models describing files and images. """
from __future__ import annotations

import sedate

from datetime import datetime
from dateutil.relativedelta import relativedelta
from functools import cached_property
from itertools import chain, groupby
from onegov.core.orm import as_selectable
from onegov.core.orm.mixins import dict_property, meta_property
from onegov.file import File, FileSet, FileCollection, FileSetCollection
from onegov.file import SearchableFile
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.form.validators import WhitelistedMimeType
from onegov.org import _
from onegov.org.models.extensions import AccessExtension
from onegov.org.utils import widest_access
from onegov.search import ORMSearchable
from operator import attrgetter, itemgetter
from sedate import standardize_date, utcnow
from sqlalchemy import asc, desc, select, nullslast

from typing import (
    overload, Any, Generic, Literal, NamedTuple, TypeVar, TYPE_CHECKING)
if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from sqlalchemy.engine import Result
    from sqlalchemy.orm import Query, Session
    from sqlalchemy.sql import Select
    from typing import Self

    _T = TypeVar('_T')
    _RowT = TypeVar('_RowT')

    class IdRow(NamedTuple):
        id: str

    class FileRow(NamedTuple):
        number: int
        id: str
        name: str
        order: str
        signed: bool
        upload_date: datetime
        publish_end_date: datetime
        content_type: str


FileT = TypeVar('FileT', bound=File)


class DateInterval(NamedTuple):
    name: str
    start: datetime
    end: datetime


class GroupFilesByDateMixin(Generic[FileT]):

    if TYPE_CHECKING:
        def query(self) -> Query[FileT]: ...

    def get_date_intervals(
        self,
        today: datetime
    ) -> Iterator[DateInterval]:

        today = standardize_date(today, 'UTC')
        month_end = today + relativedelta(day=31)
        month_start = today - relativedelta(day=1)
        next_month_start = month_start + relativedelta(months=1)
        in_distant_future = next_month_start + relativedelta(years=100)

        yield DateInterval(
            name=_('In future'),
            start=next_month_start,
            end=in_distant_future)

        yield DateInterval(
            name=_('This month'),
            start=month_start,
            end=month_end)

        last_month_end = month_start - relativedelta(microseconds=1)
        last_month_start = month_start - relativedelta(months=1)

        yield DateInterval(
            name=_('Last month'),
            start=last_month_start,
            end=last_month_end)

        if month_start.month not in (1, 2):
            this_year_end = last_month_start - relativedelta(microseconds=1)
            this_year_start = this_year_end.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

            yield DateInterval(
                name=_('This year'),
                start=this_year_start,
                end=this_year_end)
        else:
            this_year_end = None
            this_year_start = None

        last_year_end = this_year_start or last_month_start
        last_year_end -= relativedelta(microseconds=1)
        last_year_start = last_year_end.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        yield DateInterval(
            name=_('Last year'),
            start=last_year_start,
            end=last_year_end)

        older_end = last_year_start - relativedelta(microseconds=1)
        older_start = datetime(2000, 1, 1, tzinfo=today.tzinfo)

        yield DateInterval(
            name=_('Older'),
            start=older_start,
            end=older_end)

    @overload
    def query_intervals(
        self,
        intervals: Iterable[DateInterval],
        before_filter: Callable[[Query[FileT]], Query[_RowT]],
        process: Callable[[_RowT], _T]
    ) -> Iterator[tuple[str, _T]]: ...

    @overload
    def query_intervals(
        self,
        intervals: Iterable[DateInterval],
        before_filter: None,
        process: Callable[[FileT], _T]
    ) -> Iterator[tuple[str, _T]]: ...

    @overload
    def query_intervals(
        self,
        intervals: Iterable[DateInterval],
        before_filter: None = None,
        *,
        process: Callable[[FileT], _T]
    ) -> Iterator[tuple[str, _T]]: ...

    @overload
    def query_intervals(
        self,
        intervals: Iterable[DateInterval],
        before_filter: Callable[[Query[FileT]], Query[Any]] | None = None,
        process: None = None
    ) -> Iterator[tuple[str, Any]]: ...

    def query_intervals(
        self,
        intervals: Iterable[DateInterval],
        before_filter: Callable[[Query[FileT]], Query[Any]] | None = None,
        process: Callable[[Any], Any] | None = None
    ) -> Iterator[tuple[str, Any]]:

        base_query = self.query().order_by(desc(File.created))

        if before_filter:
            base_query = before_filter(base_query)

        for interval in intervals:
            query = base_query.filter(File.created >= interval.start)
            query = query.filter(File.created <= interval.end)

            for result in query.all():
                if process is not None:
                    yield interval.name, process(result)

    @overload
    def grouped_by_date(
        self,
        today: datetime | None = None,
        id_only: Literal[True] = True
    ) -> groupby[str, tuple[str, str]]: ...

    @overload
    def grouped_by_date(
        self,
        today: datetime | None,
        id_only: Literal[False]
    ) -> groupby[str, tuple[str, FileT]]: ...

    @overload
    def grouped_by_date(
        self,
        today: datetime | None = None,
        *,
        id_only: Literal[False]
    ) -> groupby[str, tuple[str, FileT]]: ...

    def grouped_by_date(
        self,
        today: datetime | None = None,
        id_only: bool = True
    ) -> groupby[str, tuple[str, FileT | str]]:
        """ Returns all files grouped by natural language dates.

        By default, only ids are returned, as this is enough to build the
        necessary links, which is what you usually want from a file.

        The given date is expected to be in UTC.

        """

        intervals = tuple(self.get_date_intervals(today or utcnow()))

        files: Iterator[tuple[str, str | FileT]]
        if id_only:
            def before_filter(query: Query[FileT]) -> Query[IdRow]:
                return query.with_entities(File.id)

            def process(result: IdRow) -> str:
                return result.id

            files = self.query_intervals(intervals, before_filter, process)
        else:
            def process_file(result: FileT) -> FileT:
                return result

            files = self.query_intervals(intervals, None, process_file)

        return groupby(files, key=itemgetter(0))


class GeneralFile(File, SearchableFile):
    __mapper_args__ = {'polymorphic_identity': 'general'}

    fts_type_title = _('Files')

    #: the access of all the linked models
    linked_accesses: dict_property[dict[str, str]] = (
        meta_property(default=dict)
    )

    @property
    def access(self) -> str:
        if self.publication:
            return 'public'

        if not self.linked_accesses:
            # a file which is not a publication and has no linked
            # accesses is considered secret
            return 'secret'

        return widest_access(*self.linked_accesses.values())


class ImageFile(File):
    __mapper_args__ = {'polymorphic_identity': 'image'}


class ImageSet(FileSet, AccessExtension, ORMSearchable):
    __mapper_args__ = {'polymorphic_identity': 'image'}

    fts_type_title = _('Photo Albums')
    fts_public = True
    fts_title_property = 'title'
    fts_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
        'lead': {'type': 'localized', 'weight': 'B'}
    }

    lead: dict_property[str | None] = meta_property()
    view: dict_property[str | None] = meta_property()

    order: dict_property[str] = meta_property(default='by-last-change')
    order_direction: dict_property[str] = meta_property(default='desc')

    show_images_on_homepage: dict_property[bool | None] = meta_property()

    @property
    def ordered_files(self) -> list[File]:
        if self.order == 'by-last-change':
            # the files are already sorted, since this relationship
            # is sorted by last change in descending order
            if self.order_direction == 'desc':
                return self.files
            else:
                return [*reversed(self.files)]

        sort_key: Callable[[File], str]
        if self.order == 'by-name':
            sort_key = attrgetter('name')
        elif self.order == 'by-caption':
            # we can't use attrgetter since note is nullable
            def sort_key(file: File) -> str:
                return file.note or ''
        else:
            raise AssertionError('unreachable')

        # for the rest we sort by attribute name
        return sorted(
            self.files,
            key=sort_key,
            reverse=self.order_direction == 'desc'
        )


class ImageSetCollection(FileSetCollection[ImageSet]):

    def __init__(self, session: Session) -> None:
        super().__init__(session, type='image')


class GeneralFileCollection(
    FileCollection[GeneralFile],
    GroupFilesByDateMixin[GeneralFile]
):

    supported_content_types = WhitelistedMimeType.whitelist

    file_list = as_selectable("""
        SELECT
            row_number() OVER () as number, -- Integer
            id,                             -- Text
            name,                           -- Text
            "order",                        -- Text
            signed,                         -- Boolean
            created as upload_date,         -- UTCDateTime
            publish_end_date,               -- UTCDateTime
            reference->>'content_type'
                AS content_type             -- Text
        FROM files
        WHERE type = 'general'
    """)

    def __init__(self, session: Session, order_by: str = 'name') -> None:
        super().__init__(session, type='general', allow_duplicates=False)

        self.order_by = order_by
        self.direction = order_by == 'name' and 'ascending' or 'descending'

        self._last_interval: DateInterval | None = None

    def for_order(self, order: str) -> Self:
        return self.__class__(self.session, order_by=order)

    @cached_property
    def intervals(self) -> tuple[DateInterval, ...]:
        return tuple(self.get_date_intervals(today=sedate.utcnow()))

    @property
    def statement(self) -> Select[FileRow]:
        stmt = select(*self.file_list.c)

        if self.order_by == 'name':
            order = self.file_list.c.order
        elif self.order_by == 'date':
            order = self.file_list.c.upload_date
        elif self.order_by == 'publish_end_date':
            order = self.file_list.c.publish_end_date
        else:
            order = self.file_list.c.order

        direction = asc if self.direction == 'ascending' else desc

        return stmt.order_by(nullslast(direction(order)))

    @property
    def files(self) -> Result[FileRow]:
        return self.session.execute(self.statement)

    def group(self, record: FileRow) -> str:

        def get_first_character(record: FileRow) -> str:
            if record.order[0].isdigit():
                return '0-9'
            return record.order[0].upper()

        if self.order_by == 'name':
            return get_first_character(record)
        elif self.order_by == 'date' or self.order_by == 'publish_end_date':
            intervals: Iterable[DateInterval]
            if self._last_interval:
                intervals = chain((self._last_interval, ), self.intervals)
            else:
                intervals = self.intervals

            if self.order_by == 'date':
                for interval in intervals:
                    if interval.start <= record.upload_date <= interval.end:
                        break
                else:
                    return _('Older')
            elif self.order_by == 'publish_end_date':
                for interval in intervals:
                    if not record.publish_end_date:
                        return _('None')
                    if (interval.start <= record.publish_end_date
                            <= interval.end):
                        break
                else:
                    return _('Older')

            # this method is usually called for each item in a sorted set,
            # we optimise for that by caching the last matching interval
            # and checking that one first the next time
            self._last_interval = interval

            return interval.name

        else:
            # default ordering by name
            return get_first_character(record)


class BaseImageFileCollection(
    FileCollection[FileT],
    GroupFilesByDateMixin[FileT]
):

    supported_content_types = IMAGE_MIME_TYPES_AND_SVG


class ImageFileCollection(BaseImageFileCollection[ImageFile]):

    def __init__(self, session: Session) -> None:
        super().__init__(session, type='image', allow_duplicates=False)
