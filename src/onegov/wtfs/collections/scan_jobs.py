from onegov.core.collection import Pagination
from onegov.core.orm.func import unaccent
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import ScanJob
from sqlalchemy import func
from sqlalchemy import or_


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from datetime import date
    from sqlalchemy.orm import Query, Session
    from typing import Self
    from uuid import UUID


class ScanJobCollection(Pagination[ScanJob]):

    # FIXME: Pagination expects page to be always set
    #        if we want it to be optional it needs to use
    #        page_index everywhere consistently
    page: int | None  # type: ignore[assignment]
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
        session: 'Session',
        page: int = 0,
        group_id: str | None = None,
        from_date: 'date | None' = None,
        to_date: 'date | None' = None,
        type: 'Collection[str] | None' = None,
        municipality_id: 'Collection[UUID | str] | None' = None,
        term: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None
    ):
        super().__init__(page)
        self.session = session
        self.group_id = group_id
        self.from_date = from_date
        self.to_date = to_date
        self.type = type
        self.municipality_id = municipality_id
        self.term = term
        self.sort_by = sort_by
        self.sort_order = sort_order

    def next_delivery_number(
        self,
        municipality_id: 'UUID | str | None'
    ) -> int:
        """ Returns the next delivery number for the given municipality. """
        query = self.session.query(func.max(ScanJob.delivery_number))
        query = query.filter_by(municipality_id=municipality_id)
        return (query.scalar() or 0) + 1

    def add(self, **kwargs: Any) -> ScanJob:
        """ Adds a new scan job. """

        if 'delivery_number' not in kwargs:
            kwargs['delivery_number'] = self.next_delivery_number(
                kwargs.get('municipality_id')
            )

        scan_job = ScanJob(**kwargs)
        self.session.add(scan_job)
        self.session.flush()
        return scan_job

    def subset(self) -> 'Query[ScanJob]':
        return self.query()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScanJobCollection):
            return False

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

    def default(self) -> 'Self':
        """ Returns the jobs unfiltered and ordered by default. """

        return self.__class__(self.session, group_id=self.group_id)

    @property
    def page_index(self) -> int:
        """ The current page. """

        return self.page or 0

    def page_by_index(self, page: int) -> 'Self':
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

    def sort_order_by_key(self, sort_by: str) -> str:
        """ Returns the sort order by key.

        Defaults to 'unsorted'.

        """

        if self.current_sort_by == sort_by:
            return self.current_sort_order
        return 'unsorted'

    def by_order(self, sort_by: str) -> 'Self':
        """ Returns the jobs ordered by the given key. """

        sort_order = self.default_sort_order
        if sort_by == self.current_sort_by:
            if self.current_sort_order == 'ascending':
                sort_order = 'descending'
            else:
                sort_order = 'ascending'

        return self.__class__(
            self.session,
            page=0,
            group_id=self.group_id,
            from_date=self.from_date,
            to_date=self.to_date,
            type=self.type,
            municipality_id=self.municipality_id,
            term=self.term,
            sort_by=sort_by,
            sort_order=sort_order
        )

    # FIXME: Return the correct type
    @property
    def order_by(self) -> Any:
        """ Returns an SqlAlchemy expression for ordering queries based
        on the current sorting key and ordering.

        """

        result: Any
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
    def offset(self) -> int:
        """ The current position in the batch. """

        return (self.page or 0) * self.batch_size

    @property
    def previous(self) -> 'Self | None':
        """ The previous page. """

        if (self.page or 0) > 0:
            return self.page_by_index((self.page or 0) - 1)
        return None

    @property
    def next(self) -> 'Self | None':
        """ The next page. """

        if (self.page or 0) + 1 < self.pages_count:
            return self.page_by_index((self.page or 0) + 1)
        return None

    def query(self) -> 'Query[ScanJob]':
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

    def by_id(self, id: 'UUID') -> ScanJob | None:
        """ Returns the scan job with the given ID. """
        return self.query().filter(ScanJob.id == id).first()

    def delete(self, scan_job: ScanJob) -> None:
        """ Deletes the given scan job. """
        self.session.delete(scan_job)
        self.session.flush()
