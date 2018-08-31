from cached_property import cached_property
from csv import writer
from onegov.core.collection import Pagination
from onegov.swissvotes.fields.dataset import COLUMNS
from onegov.swissvotes.fields.dataset import DatasetDialect
from onegov.swissvotes.models import PolicyArea
from onegov.swissvotes.models import SwissVote
from sqlalchemy import or_


class SwissVoteCollection(Pagination):

    batch_size = 20
    initial_sort_by = 'date'
    initial_sort_order = 'descending'
    default_sort_order = 'ascending'

    SORT_BYS = ('date', 'legal_form', 'result', 'result_people_yeas_p',
                'title')
    SORT_ORDERS = ('ascending', 'descending')

    def __init__(
        self,
        session,
        page=None,
        from_date=None,
        to_date=None,
        legal_form=None,
        result=None,
        policy_area=None,
        sort_by=None,
        sort_order=None
    ):
        self.session = session
        self.page = page
        self.from_date = from_date
        self.to_date = to_date
        self.legal_form = legal_form
        self.result = result
        self.policy_area = policy_area
        self.sort_by = sort_by
        self.sort_order = sort_order

    def subset(self):
        return self.query()

    def __eq__(self, other):
        return (
            (self.page or 0) == (other.page or 0) and
            (self.from_date or None) == (other.from_date or None) and
            (self.to_date or None) == (other.to_date or None) and
            set(self.legal_form or []) == set(other.legal_form or []) and
            set(self.result or []) == set(other.result or []) and
            set(self.policy_area or []) == set(other.policy_area or []) and
            (self.sort_by or None) == (other.sort_by or None) and
            (self.sort_order or None) == (other.sort_order or None)
        )

    @property
    def page_index(self):
        """ The current page. """

        return self.page or 0

    def page_by_index(self, page):
        """ Returns the requested page. """

        return self.__class__(
            self.session,
            page=page,
            from_date=self.from_date,
            to_date=self.to_date,
            legal_form=self.legal_form,
            result=self.result,
            policy_area=self.policy_area,
            sort_by=self.sort_by,
            sort_order=self.sort_order
        )

    @property
    def current_sort_by(self):
        """ Returns the currently used sorting key.

        Defaults to a reasonable value.

        """
        result = self.initial_sort_by if self.sort_by is None else self.sort_by
        return result if result in self.SORT_BYS else self.initial_sort_by

    @property
    def current_sort_order(self):
        """ Returns the currently used sorting order.

        Defaults to a reasonable value.

        """

        default = self.default_sort_order
        default = self.initial_sort_order if self.sort_by is None else default
        result = default if self.sort_order is None else self.sort_order
        return result if result in self.SORT_ORDERS else default

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
            self.session,
            page=None,
            from_date=self.from_date,
            to_date=self.to_date,
            legal_form=self.legal_form,
            result=self.result,
            policy_area=self.policy_area,
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
            result = unaccent(SwissVote.title)
        else:
            result = (
                getattr(SwissVote, f'_{self.current_sort_by}', None) or
                getattr(SwissVote, self.current_sort_by, None)
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

    def query(self):
        """ Returns the votes matching to the current filters and order. """

        query = self.session.query(SwissVote)

        if self.from_date:
            query = query.filter(SwissVote.date >= self.from_date)
        if self.to_date:
            query = query.filter(SwissVote.date <= self.to_date)
        if self.legal_form:
            query = query.filter(SwissVote._legal_form.in_(self.legal_form))
        if self.result:
            query = query.filter(
                SwissVote._result.in_(self.result)
            )
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

        query = query.order_by(self.order_by)

        return query

    def by_bfs_number(self, bfs_number):
        """ Returns the vote with the given BFS number. """

        query = self.query().filter(SwissVote.bfs_number == bfs_number)
        return query.first()

    @cached_property
    def available_descriptors(self):
        """ Returns a list of the used descriptor values (level 1-3). """

        # todo: optimize
        return[
            [
                x[0] for x in (
                    set(self.session.query(SwissVote.descriptor_1_level_1)) |
                    set(self.session.query(SwissVote.descriptor_2_level_1)) |
                    set(self.session.query(SwissVote.descriptor_2_level_1))
                ) if x[0]
            ],
            [
                x[0] for x in (
                    set(self.session.query(SwissVote.descriptor_1_level_2)) |
                    set(self.session.query(SwissVote.descriptor_2_level_2)) |
                    set(self.session.query(SwissVote.descriptor_2_level_2))
                ) if x[0]
            ],
            [
                x[0] for x in (
                    set(self.session.query(SwissVote.descriptor_1_level_3)) |
                    set(self.session.query(SwissVote.descriptor_2_level_3)) |
                    set(self.session.query(SwissVote.descriptor_2_level_3))
                ) if x[0]
            ]
        ]

    def update(self, votes):
        """ Adds or updates the given votes. """

        for vote in votes:
            old = self.query().filter_by(bfs_number=vote.bfs_number).first()
            if old:
                for attribute in COLUMNS.keys():
                    setattr(old, attribute, getattr(vote, attribute))
            else:
                self.session.add(vote)

    def export(self, file):
        """ Exports all votes according to the code book. """

        csv = writer(file, dialect=DatasetDialect())
        csv.writerow(COLUMNS.values())

        for vote in self.query().order_by(None).order_by(SwissVote.bfs_number):
            row = []
            for attribute, column in COLUMNS.items():
                value = getattr(vote, attribute)
                type_ = str(vote.__table__.columns[attribute.lstrip('_')].type)
                if value is None:
                    row.append('.')
                elif type_ == 'TEXT':
                    row.append(value)
                elif type_ == 'DATE':
                    row.append(f'{value:%d.%m.%Y}')
                elif type_ == 'INTEGER':
                    row.append(str(value))
                elif type_ == 'INT4RANGE':
                    row.append(f'{value.lower}-{value.upper}')
                elif type_.startswith('NUMERIC'):
                    row.append(
                        f'{value:f}'.replace('.', ',').rstrip('0').rstrip(',')
                    )
            csv.writerow(row)
