from cached_property import cached_property
from csv import writer
from datetime import date
from decimal import Decimal
from decimal import InvalidOperation
from onegov.core.collection import Pagination
from onegov.swissvotes.models import ColumnMapper
from onegov.swissvotes.models import PolicyArea
from onegov.swissvotes.models import SwissVote
from psycopg2.extras import NumericRange
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import undefer_group
from xlsxwriter.workbook import Workbook


class SwissVoteCollection(Pagination):

    """ A collection of votes.

    Supports pagination, filtering, sorting, exporting (CSV/XLSX) and batch
    adding/updating.

    """

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
        app,
        page=None,
        from_date=None,
        to_date=None,
        legal_form=None,
        result=None,
        policy_area=None,
        term=None,
        full_text=None,
        position_federal_council=None,
        position_national_council=None,
        position_council_of_states=None,
        sort_by=None,
        sort_order=None
    ):
        self.app = app
        self.session = app.session()
        self.page = page
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

    def add(self, **kwargs):
        vote = SwissVote(**kwargs)
        self.session.add(vote)
        self.session.flush()
        return vote

    def subset(self):
        return self.query()

    def __eq__(self, other):
        return (
            (self.page or 0) == (other.page or 0)
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

    def default(self):
        """ Returns the votes unfiltered and ordered by default. """

        return self.__class__(self.app)

    @property
    def page_index(self):
        """ The current page. """

        return self.page or 0

    def page_by_index(self, page):
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
    def current_sort_by(self):
        """ Returns the currently used sorting key.

        Defaults to a reasonable value.

        """
        if self.sort_by in self.SORT_BYS:
            return self.sort_by

        return self.initial_sort_by

    @property
    def current_sort_order(self):
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

    def sort_order_by_key(self, sort_by):
        """ Returns the sort order by key.

        Defaults to 'unsorted'.

        """

        if self.current_sort_by == sort_by:
            return self.current_sort_order
        return 'unsorted'

    def by_order(self, sort_by):
        """ Returns the votes ordered by the given key. """

        sort_order = self.default_sort_order
        if sort_by == self.current_sort_by:
            if self.current_sort_order == 'ascending':
                sort_order = 'descending'
            else:
                sort_order = 'ascending'

        return self.__class__(
            self.app,
            page=None,
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
    def order_by(self):
        """ Returns an SqlAlchemy expression for ordering queries based
        on the current sorting key and ordering.

        """

        if self.current_sort_by == 'title':
            from onegov.core.orm.func import unaccent
            if self.app.session_manager.current_locale == 'fr_CH':
                result = unaccent(SwissVote.short_title_fr)
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
    def offset(self):
        """ The current position in the batch. """

        return (self.page or 0) * self.batch_size

    @property
    def previous(self):
        """ The previous page. """

        if (self.page or 0) - 1 >= 0:
            return self.page_by_index((self.page or 0) - 1)

    @property
    def next(self):
        """ The next page. """

        if (self.page or 0) + 1 < self.pages_count:
            return self.page_by_index((self.page or 0) + 1)

    @property
    def term_expression(self):
        """ Returns the current search term transformed to use within
        Postgres ``to_tsquery`` function.


        Removes all unwanted characters, replaces prefix matching, joins
        word together using FOLLOWED BY.
        """

        def cleanup(text):
            result = ''.join((c for c in text if c.isalnum() or c in ',.'))
            return f'{result}:*' if text.endswith('*') else result

        parts = [cleanup(part) for part in (self.term or '').split()]
        return ' <-> '.join([part for part in parts if part])

    @property
    def term_filter_numeric(self):
        """ Returns a list of SqlAlchemy filter statements matching possible
        numeric attributes based on the term.

        """

        result = []
        if self.term:
            for part in self.term.split():
                if part.replace('.', '').isnumeric():
                    number = Decimal(part)
                    result.append(SwissVote.bfs_number == number)
                    result.append(SwissVote.procedure_number == number)

        return result

    @property
    def term_filter_text(self):
        """ Returns a list of SqlAlchemy filter statements matching possible
        fulltext attributes based on the term.

        """
        term = self.term_expression

        if not term:
            return []

        def match(column, language='german'):
            return column.op('@@')(func.to_tsquery(language, term))

        def match_convert(column, language='german'):
            return match(func.to_tsvector(language, column), language)

        if not self.full_text:
            return [
                match_convert(SwissVote.title_de),
                match_convert(SwissVote.title_fr, 'french'),
                match_convert(SwissVote.short_title_de),
                match_convert(SwissVote.short_title_fr, 'french'),
                match_convert(SwissVote.keyword),
            ]
        return [
            match_convert(SwissVote.title_de),
            match_convert(SwissVote.title_fr, 'french'),
            match_convert(SwissVote.short_title_de),
            match_convert(SwissVote.short_title_fr, 'french'),
            match_convert(SwissVote.keyword),
            match_convert(SwissVote.initiator),
            match(SwissVote.searchable_text_de_CH),
            match(SwissVote.searchable_text_fr_CH, 'french'),
        ]

    @property
    def term_filter(self):
        """ Returns a list of SqlAlchemy filter statements based on the search
        term.

        """

        return self.term_filter_numeric + self.term_filter_text

    def query(self):
        """ Returns the votes matching to the current filters and order. """

        query = self.session.query(SwissVote)

        def in_or_none(column, values):
            statement = column.in_(values)
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
            query = query.filter(SwissVote._result.in_(self.result))
        if self.policy_area:
            levels = [[], [], []]
            for area in self.policy_area:
                area = PolicyArea(area)
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
                    self.position_federal_council
                )
            )
        if self.position_national_council:
            query = query.filter(
                in_or_none(
                    SwissVote._position_national_council,
                    self.position_national_council
                )
            )
        if self.position_council_of_states:
            query = query.filter(
                in_or_none(
                    SwissVote._position_council_of_states,
                    self.position_council_of_states
                )
            )

        query = query.order_by(self.order_by)

        return query

    def by_bfs_number(self, bfs_number):
        """ Returns the vote with the given BFS number. """
        try:
            bfs_number = Decimal(bfs_number)
        except InvalidOperation:
            return None

        query = self.query().filter(SwissVote.bfs_number == bfs_number)
        return query.first()

    @cached_property
    def available_descriptors(self):
        """ Returns a list of the used descriptor values (level 1-3). """

        query = self.session.query
        return [
            set([
                x[0] for x in query(SwissVote.descriptor_1_level_1).union(
                    query(SwissVote.descriptor_2_level_1),
                    query(SwissVote.descriptor_3_level_1)
                ).all() if x[0]
            ]),
            set([
                x[0] for x in query(SwissVote.descriptor_1_level_2).union(
                    query(SwissVote.descriptor_2_level_2),
                    query(SwissVote.descriptor_3_level_2)
                ).all() if x[0]
            ]),
            set([
                x[0] for x in query(SwissVote.descriptor_1_level_3).union(
                    query(SwissVote.descriptor_2_level_3),
                    query(SwissVote.descriptor_3_level_3)
                ).all() if x[0]
            ]),
        ]

    def update(self, votes):
        """ Adds or updates the given votes. """

        added = 0
        updated = 0
        query = self.session.query(SwissVote).options(undefer_group("dataset"))
        existing = {vote.bfs_number: vote for vote in query}
        mapper = ColumnMapper()
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

    @property
    def last_modified(self):
        """ Returns the last change of any votes. """
        return self.session.query(func.max(SwissVote.last_change)).scalar()

    def export_csv(self, file):
        """ Exports all votes according to the code book. """
        mapper = ColumnMapper()

        csv = writer(file)
        csv.writerow(mapper.columns.values())

        query = self.query().options(undefer_group("dataset"))
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
                elif isinstance(value, NumericRange):
                    row.append(f'{value.lower}-{value.upper}')
                elif isinstance(value, Decimal):
                    row.append(
                        f'{value:f}'.replace('.', ',').rstrip('0').rstrip(',')
                    )
            csv.writerow(row)

    def export_xlsx(self, file):
        """ Exports all votes according to the code book. """
        mapper = ColumnMapper()

        workbook = Workbook(file, {'default_date_format': 'dd.mm.yyyy'})
        worksheet = workbook.add_worksheet()
        worksheet.write_row(0, 0, mapper.columns.values())

        query = self.query().options(undefer_group("dataset"))
        query = query.order_by(None).order_by(SwissVote.bfs_number)

        row = 0
        for vote in query:
            row += 1
            for column_, value in enumerate(mapper.get_values(vote)):
                if value is None:
                    pass
                elif isinstance(value, str):
                    worksheet.write_string(row, column_, value)
                elif isinstance(value, date):
                    worksheet.write_datetime(row, column_, value)
                elif isinstance(value, int) or isinstance(value, Decimal):
                    worksheet.write_number(row, column_, value)
                elif isinstance(value, NumericRange):
                    worksheet.write_string(
                        row, column_, f'{value.lower}-{value.upper}'
                    )

        workbook.close()
