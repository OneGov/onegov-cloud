from onegov.core.collection import Pagination
from onegov.core.orm.func import unaccent
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import ScanJob
from sqlalchemy import or_


class ScanJobCollection(Pagination):

    batch_size = 20
    initial_sort_by = 'dispatch_date'
    initial_sort_order = 'descending'
    default_sort_order = 'ascending'

    SORT_BYS = (
        'dispatch_date',
        'delivery_number',
        'municipality_id'
    )
    SORT_ORDERS = ('ascending', 'descending')

    def __init__(
        self,
        session,
        page=None,
        group_id=None,
        from_date=None,
        to_date=None,
        type=None,
        municipality_id=None,
        term=None,
        sort_by=None,
        sort_order=None
    ):
        self.session = session
        self.page = page
        self.group_id = group_id
        self.from_date = from_date
        self.to_date = to_date
        self.type = type
        self.municipality_id = municipality_id
        self.term = term
        self.sort_by = sort_by
        self.sort_order = sort_order

    def add(self, **kwargs):
        """ Adds a new scan job. """

        scan_job = ScanJob(**kwargs)
        self.session.add(scan_job)
        self.session.flush()
        return scan_job

    def subset(self):
        return self.query()

    def __eq__(self, other):
        return (
            (self.page or 0) == (other.page or 0)
            and (self.group_id or None) == (other.group_id or None)
            and (self.from_date or None) == (other.from_date or None)
            and (self.to_date or None) == (other.to_date or None)
            and set(self.type or []) == set(other.type or [])
            and (
                set(self.municipality_id or [])
                == set(other.municipality_id or [])
            )
            and (self.term or None) == (other.term or None)
            and (self.sort_by or None) == (other.sort_by or None)
            and (self.sort_order or None) == (other.sort_order or None)
        )

    def default(self):
        """ Returns the jobs unfiltered and ordered by default. """

        return self.__class__(self.session, group_id=self.group_id)

    @property
    def page_index(self):
        """ The current page. """

        return self.page or 0

    def page_by_index(self, page):
        """ Returns the requested page. """

        return self.__class__(
            self.session,
            page=page,
            group_id=self.group_id,
            from_date=self.from_date,
            to_date=self.to_date,
            type=self.type,
            municipality_id=self.municipality_id,
            term=self.term,
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
        """ Returns the jobs ordered by the given key. """

        sort_order = self.default_sort_order
        if sort_by == self.current_sort_by:
            if self.current_sort_order == 'ascending':
                sort_order = 'descending'
            else:
                sort_order = 'ascending'

        return self.__class__(
            self.session,
            page=None,
            group_id=self.group_id,
            from_date=self.from_date,
            to_date=self.to_date,
            type=self.type,
            municipality_id=self.municipality_id,
            term=self.term,
            sort_by=sort_by,
            sort_order=sort_order
        )

    @property
    def order_by(self):
        """ Returns an SqlAlchemy expression for ordering queries based
        on the current sorting key and ordering.

        """

        if self.current_sort_by == 'municipality_id':
            result = unaccent(Municipality.name)
        else:
            result = getattr(ScanJob, self.current_sort_by, None)
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
        """ Returns the jobs matching to the current filters and order. """

        query = self.session.query(ScanJob)
        query = query.join(Municipality)

        if self.group_id:
            query = query.filter(ScanJob.municipality_id == self.group_id)
        elif self.municipality_id:
            query = query.filter(
                ScanJob.municipality_id.in_(self.municipality_id)
            )
        if self.from_date:
            query = query.filter(ScanJob.dispatch_date >= self.from_date)
        if self.to_date:
            query = query.filter(ScanJob.dispatch_date <= self.to_date)
        if self.type:
            query = query.filter(ScanJob.type.in_(self.type))
        if self.term:
            query = query.filter(
                or_(*[
                    ScanJob.dispatch_note.ilike(f'%{self.term}%'),
                    ScanJob.return_note.ilike(f'%{self.term}%')
                ])
            )

        query = query.order_by(self.order_by)

        return query

    def by_id(self, id):
        """ Returns the scan job with the given ID. """
        return self.query().filter(ScanJob.id == id).first()

    def delete(self, scan_job):
        """ Deletes the given scan job. """
        self.session.delete(scan_job)
        self.session.flush()
