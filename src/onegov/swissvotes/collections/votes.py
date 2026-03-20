from __future__ import annotations

from csv import writer
from datetime import date
from decimal import Decimal
from decimal import InvalidOperation
from functools import cached_property
from onegov.core.collection import Pagination
from onegov.swissvotes.models import ColumnMapperDataset
from onegov.swissvotes.models import PolicyArea
from onegov.swissvotes.models import SwissVote
from sqlalchemy import func
from sqlalchemy import literal_column
from sqlalchemy import or_
from xlsxwriter.workbook import Workbook


from typing import Any
from typing import IO
from typing import TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from onegov.swissvotes.app import SwissvotesApp
    from sqlalchemy.orm import Query
    from sqlalchemy.sql.elements import ColumnElement, SQLCoreOperations
    from typing import Self

T = TypeVar('T')


class SwissVoteCollection(Pagination[SwissVote]):

    """ A collection of votes.

    Supports pagination, filtering, sorting, exporting (CSV/XLSX) and batch
    adding/updating.

    """

    page: int | None  # type:ignore[assignment]
    batch_size = 20
    initial_sort_by = 'date'
    initial_sort_order = 'descending'
    default_sort_order = 'ascending'

    SORT_BYS = (
        'date',
        'legal_form',
        'result',
        'result_people_yeas_p',
        'title',
        'result_turnout'
    )
    SORT_ORDERS = ('ascending', 'descending')

    def __init__(
        self,
        app: SwissvotesApp,
        page: int = 0,
        from_date: date | None = None,
        to_date: date | None = None,
        legal_form: list[int] | None = None,
        result: list[int] | None = None,
        policy_area: list[str] | None = None,
        term: str | None = None,
        full_text: bool | None = None,
        position_federal_council: list[int] | None = None,
        position_national_council: list[int] | None = None,
        position_council_of_states: list[int] | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None
    ) -> None:
        super().__init__(page)
        self.app = app
        self.session = app.session()
        self.from_date = from_date
        self.to_date = to_date
        self.legal_form = legal_form
        self.result = result
        self.policy_area = policy_area
        self.term = term
        self.full_text = full_text
        self.position_federal_council = position_federal_council
        self.position_national_council = position_national_council
        self.position_council_of_states = position_council_of_states
        self.sort_by = sort_by
        self.sort_order = sort_order

    def add(self, **kwargs: Any) -> SwissVote:
        vote = SwissVote(**kwargs)
        self.session.add(vote)
        self.session.flush()
        return vote

    def subset(self) -> Query[SwissVote]:
        return self.query()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and (self.page or 0) == (other.page or 0)
            and (self.from_date or None) == (other.from_date or None)
            and (self.to_date or None) == (other.to_date or None)
            and set(self.legal_form or []) == set(other.legal_form or [])
            and set(self.result or []) == set(other.result or [])
            and set(self.policy_area or []) == set(other.policy_area or [])
            and (self.term or None) == (other.term or None)
            and (self.full_text or None) == (other.full_text or None)
            and (
                (self.position_federal_council or [])
                == (other.position_federal_council or [])
            )
            and (
                (self.position_national_council or [])
                == (other.position_national_council or [])
            )
            and (
                (self.position_council_of_states or [])
                == (other.position_council_of_states or [])
            )
            and (self.sort_by or None) == (other.sort_by or None)
            and (self.sort_order or None) == (other.sort_order or None)
        )

    def default(self) -> Self:
        """ Returns the votes unfiltered and ordered by default. """

        return self.__class__(self.app)

    @property
    def page_index(self) -> int:
        """ The current page. """

        return self.page or 0

    def page_by_index(self, page: int) -> Self:
        """ Returns the requested page. """

        return self.__class__(
            self.app,
            page=page,
            from_date=self.from_date,
            to_date=self.to_date,
            legal_form=self.legal_form,
            result=self.result,
            policy_area=self.policy_area,
            term=self.term,
            full_text=self.full_text,
            position_federal_council=self.position_federal_council,
            position_national_council=self.position_national_council,
            position_council_of_states=self.position_council_of_states,
            sort_by=self.sort_by,
            sort_order=self.sort_order
        )

    @property
    def current_sort_by(self) -> str:
        """ Returns the currently used sorting key.

        Defaults to a reasonable value.

        """
        if self.sort_by in self.SORT_BYS:
            return self.sort_by

        return self.initial_sort_by

    @property
    def current_sort_order(self) -> str:
        """ Returns the currently used sorting order.

        Defaults to a reasonable value.

        """
        if self.sort_by in self.SORT_BYS:
            if self.sort_order in self.SORT_ORDERS:
                return self.sort_order

            if self.sort_by == self.initial_sort_by:
                return self.initial_sort_order

            return self.default_sort_order

        return self.initial_sort_order

    def sort_order_by_key(self, sort_by: str | None) -> str:
        """ Returns the sort order by key.

        Defaults to 'unsorted'.

        """

        if self.current_sort_by == sort_by:
            return self.current_sort_order
        return 'unsorted'

    def by_order(self, sort_by: str | None) -> Self:
        """ Returns the votes ordered by the given key. """

        sort_order = self.default_sort_order
        if sort_by == self.current_sort_by:
            if self.current_sort_order == 'ascending':
                sort_order = 'descending'
            else:
                sort_order = 'ascending'

        return self.__class__(
            self.app,
            page=0,
            from_date=self.from_date,
            to_date=self.to_date,
            legal_form=self.legal_form,
            result=self.result,
            policy_area=self.policy_area,
            term=self.term,
            full_text=self.full_text,
            position_federal_council=self.position_federal_council,
            position_national_council=self.position_national_council,
            position_council_of_states=self.position_council_of_states,
            sort_by=sort_by,
            sort_order=sort_order
        )

    @property
    def order_by(self) -> ColumnElement[Any]:
        """ Returns an SqlAlchemy expression for ordering queries based
        on the current sorting key and ordering.

        """

        result: ColumnElement[Any] | None
        if self.current_sort_by == 'title':
            from onegov.core.orm.func import unaccent
            if self.app.session_manager.current_locale == 'fr_CH':
                result = unaccent(SwissVote.short_title_fr)
            elif self.app.session_manager.current_locale == 'en_US':
                result = unaccent(SwissVote.short_title_en)
            else:
                result = unaccent(SwissVote.short_title_de)
        else:
            result = (
                getattr(SwissVote, f'_{self.current_sort_by}', None)
                or getattr(SwissVote, self.current_sort_by, None)
            )
            if not result:
                raise NotImplementedError()

        if self.current_sort_order == 'descending':
            result = result.desc()

        return result

    @property
    def offset(self) -> int:
        """ The current position in the batch. """

        return self.page_index * self.batch_size

    @property
    def previous(self) -> Self | None:
        """ The previous page. """

        if self.page_index - 1 >= 0:
            return self.page_by_index(self.page_index - 1)
        return None

    @property
    def next(self) -> Self | None:
        """ The next page. """

        if self.page_index + 1 < self.pages_count:
            return self.page_by_index(self.page_index + 1)
        return None

    @property
    def term_filter_numeric(self) -> list[ColumnElement[bool]]:
        """ Returns a list of SqlAlchemy filter statements matching possible
        numeric attributes based on the term.

        """

        result = []
        if self.term:
            for part in self.term.split():
                if part.replace('.', '', 1).isnumeric():
                    number = Decimal(part)
                    result.append(SwissVote.bfs_number == number)
                if part.replace('.', '', 1).replace('_', '', 1).isnumeric():
                    result.append(SwissVote.procedure_number == part)

        return result

    @property
    def term_filter_text(self) -> list[ColumnElement[bool]]:
        """ Returns a list of SqlAlchemy filter statements matching possible
        fulltext attributes based on the term.

        """
        term = SwissVote.search_term_expression(self.term)

        if not term:
            return []

        def match(
            column: SQLCoreOperations[str | None],
            language: str
        ) -> ColumnElement[bool]:
            return column.op('@@')(func.to_tsquery(
                literal_column(repr(language)), term))

        def match_convert(
            column: SQLCoreOperations[str | None],
            language: str
        ) -> ColumnElement[bool]:
            return match(func.to_tsvector(
                literal_column(repr(language)), column), language)

        if not self.full_text:
            return [
                match_convert(SwissVote.title_de, 'german'),
                match_convert(SwissVote.title_fr, 'french'),
                match_convert(SwissVote.short_title_de, 'german'),
                match_convert(SwissVote.short_title_fr, 'french'),
                match_convert(SwissVote.short_title_en, 'english'),
                match_convert(SwissVote.keyword, 'german'),
            ]
        return [
            match_convert(SwissVote.title_de, 'german'),
            match_convert(SwissVote.title_fr, 'french'),
            match_convert(SwissVote.short_title_de, 'german'),
            match_convert(SwissVote.short_title_fr, 'french'),
            match_convert(SwissVote.short_title_en, 'english'),
            match_convert(SwissVote.keyword, 'german'),
            match_convert(SwissVote.initiator_de, 'german'),
            match_convert(SwissVote.initiator_fr, 'french'),
            match(SwissVote.searchable_text_de_CH, 'german'),
            match(SwissVote.searchable_text_fr_CH, 'french'),
            match(SwissVote.searchable_text_it_CH, 'italian'),
            match(SwissVote.searchable_text_en_US, 'english'),
        ]

    @property
    def term_filter(self) -> list[ColumnElement[bool]]:
        """ Returns a list of SqlAlchemy filter statements based on the search
        term.

        """

        return self.term_filter_numeric + self.term_filter_text

    def query(self) -> Query[SwissVote]:
        """ Returns the votes matching to the current filters and order. """

        query = self.session.query(SwissVote)

        def in_or_none(
            column: SQLCoreOperations[T] | SQLCoreOperations[T | None],
            values: list[T],
            extra: dict[T, T] | None = None
        ) -> ColumnElement[bool]:

            extra = extra or {}
            values = values + [x for y, x in extra.items() if y in values]
            statement: ColumnElement[bool] = column.in_(values)
            if -1 in values:
                statement = or_(statement, column.is_(None))
            return statement

        if self.from_date:
            query = query.filter(SwissVote.date >= self.from_date)
        if self.to_date:
            query = query.filter(SwissVote.date <= self.to_date)
        if self.legal_form:
            query = query.filter(SwissVote._legal_form.in_(self.legal_form))
        if self.result:
            query = query.filter(or_(
                SwissVote._result.in_(self.result),
                SwissVote._result == None,
            ))
        if self.policy_area:
            levels: list[list[Decimal]] = [[], [], []]
            for area_code in self.policy_area:
                area = PolicyArea(area_code)
                if area.level == 1:
                    levels[0].append(area.descriptor_decimal)
                if area.level == 2:
                    levels[1].append(area.descriptor_decimal)
                if area.level == 3:
                    levels[2].append(area.descriptor_decimal)
            if levels[0]:
                query = query.filter(
                    or_(
                        SwissVote.descriptor_1_level_1.in_(levels[0]),
                        SwissVote.descriptor_2_level_1.in_(levels[0]),
                        SwissVote.descriptor_3_level_1.in_(levels[0])
                    )
                )
            if levels[1]:
                query = query.filter(
                    or_(
                        SwissVote.descriptor_1_level_2.in_(levels[1]),
                        SwissVote.descriptor_2_level_2.in_(levels[1]),
                        SwissVote.descriptor_3_level_2.in_(levels[1])
                    )
                )
            if levels[2]:
                query = query.filter(
                    or_(
                        SwissVote.descriptor_1_level_3.in_(levels[2]),
                        SwissVote.descriptor_2_level_3.in_(levels[2]),
                        SwissVote.descriptor_3_level_3.in_(levels[2])
                    )
                )
        if self.term:
            query = query.filter(or_(*self.term_filter))
        if self.position_federal_council:
            query = query.filter(
                in_or_none(
                    SwissVote._position_federal_council,
                    self.position_federal_council,
                    {1: 9, 2: 8}
                )
            )
        if self.position_national_council:
            query = query.filter(
                in_or_none(
                    SwissVote._position_national_council,
                    self.position_national_council,
                    {1: 9, 2: 8}
                )
            )
        if self.position_council_of_states:
            query = query.filter(
                in_or_none(
                    SwissVote._position_council_of_states,
                    self.position_council_of_states,
                    {1: 9, 2: 8}
                )
            )

        query = query.order_by(
            self.order_by,
            SwissVote.bfs_number.desc()
        )

        return query

    def by_bfs_number(self, bfs_number: Decimal | str) -> SwissVote | None:
        """ Returns the vote with the given BFS number. """
        try:
            bfs_number = Decimal(bfs_number)
        except InvalidOperation:
            return None

        query = self.query().filter(SwissVote.bfs_number == bfs_number)
        return query.first()

    def by_bfs_numbers(
        self,
        bfs_numbers: Iterable[Decimal | str]
    ) -> dict[Decimal | str, SwissVote]:
        """ Returns the votes with the given BFS numbers. """
        real_bfs_numbers = {}
        for bfs_number in bfs_numbers:
            try:
                real_bfs_numbers[Decimal(bfs_number)] = bfs_number
            except InvalidOperation:
                pass

        if not real_bfs_numbers:
            return {}

        query = self.query().filter(
            SwissVote.bfs_number.in_(real_bfs_numbers.keys())
        )
        return {
            real_bfs_numbers[vote.bfs_number]: vote
            for vote in query
        }

    @cached_property
    def available_descriptors(self) -> list[set[Decimal]]:
        """ Returns a list of the used descriptor values (level 1-3). """

        query = self.session.query
        return [
            {
                x
                for x, in query(SwissVote.descriptor_1_level_1).union(
                    query(SwissVote.descriptor_2_level_1),
                    query(SwissVote.descriptor_3_level_1)
                ).distinct()
                if x
            },
            {
                x
                for x, in query(SwissVote.descriptor_1_level_2).union(
                    query(SwissVote.descriptor_2_level_2),
                    query(SwissVote.descriptor_3_level_2)
                ).distinct()
                if x
            },
            {
                x
                for x, in query(SwissVote.descriptor_1_level_3).union(
                    query(SwissVote.descriptor_2_level_3),
                    query(SwissVote.descriptor_3_level_3)
                ).distinct()
                if x
            },
        ]

    def update(self, votes: Iterable[SwissVote]) -> tuple[int, int]:
        """ Adds or updates the given votes. """

        added = 0
        updated = 0
        query = self.session.query(SwissVote)
        existing = {vote.bfs_number: vote for vote in query}
        mapper = ColumnMapperDataset()
        for vote in votes:
            old = existing.get(vote.bfs_number)
            if old:
                changed = False
                for attribute, value in mapper.get_items(vote):
                    if mapper.get_value(old, attribute) != value:
                        mapper.set_value(old, attribute, value)
                        changed = True

                if changed:
                    updated += 1
            else:
                added += 1
                self.session.add(vote)

        return added, updated

    def update_metadata(
        self,
        metadata: dict[Decimal, dict[str, dict[str, Any]]]
    ) -> tuple[int, int]:

        added = 0
        updated = 0
        for bfs_number, files in metadata.items():
            vote = (
                self.session.query(SwissVote)
                .filter_by(bfs_number=bfs_number).first()
            )
            if vote is not None:
                for filename, data in files.items():
                    old = vote.campaign_material_metadata.get(filename)
                    if not old:
                        added += 1
                        vote.campaign_material_metadata[filename] = data
                    elif old != data:
                        updated += 1
                        vote.campaign_material_metadata[filename] = data

        return added, updated

    @property
    def last_modified(self) -> datetime | None:
        """ Returns the last change of any votes. """
        return self.session.query(func.max(SwissVote.last_change)).scalar()

    def export_csv(self, file: IO[str]) -> None:
        """ Exports all votes according to the code book. """
        mapper = ColumnMapperDataset()

        csv = writer(file)
        csv.writerow(mapper.columns.values())

        query = self.query()
        query = query.order_by(None).order_by(SwissVote.bfs_number)

        for vote in query:
            row = []
            for value in mapper.get_values(vote):
                if value is None:
                    row.append('.')
                elif isinstance(value, str):
                    row.append(value)
                elif isinstance(value, date):
                    row.append(f'{value:%d.%m.%Y}')
                elif isinstance(value, int):
                    row.append(str(value))
                elif isinstance(value, Decimal):
                    row.append(
                        f'{value:f}'.replace('.', ',').rstrip('0').rstrip(',')
                    )
            csv.writerow(row)

    def export_xlsx(self, file: IO[Any]) -> None:
        """ Exports all votes according to the code book. """
        mapper = ColumnMapperDataset()

        workbook = Workbook(file, {'default_date_format': 'dd.mm.yyyy'})
        workbook.add_worksheet('CITATION')
        worksheet = workbook.add_worksheet('DATA')
        worksheet.write_row(0, 0, mapper.columns.values())

        query = self.query()
        query = query.order_by(None).order_by(SwissVote.bfs_number)

        for row, vote in enumerate(query, start=1):
            for column, value in enumerate(mapper.get_values(vote)):
                if value is None:
                    pass
                elif isinstance(value, str):
                    worksheet.write_string(row, column, value)
                elif isinstance(value, date):
                    worksheet.write_datetime(row, column, value)
                elif isinstance(value, (int, Decimal)):
                    worksheet.write_number(row, column, value)

        workbook.close()
