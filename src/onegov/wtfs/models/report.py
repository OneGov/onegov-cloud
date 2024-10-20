from functools import cached_property
from datetime import date
from onegov.core.orm.func import unaccent
from onegov.wtfs import _
from onegov.wtfs.models.municipality import Municipality
from onegov.wtfs.models.scan_job import ScanJob
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy.sql.expression import literal_column


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


# FIXME: make these return types more specific
def sum(table: object, attribute: str) -> Any:
    result = func.coalesce(func.sum(getattr(table, attribute)), 0)
    result = func.cast(result, Integer)
    return result.label(attribute)


def zero(attribute: str) -> Any:
    return literal_column('0').label(attribute)


class Report:
    """ The base class for the reports.

    Aggregates the ``columns_dispatch`` on the dispatch date and
    ``columns_return`` on the return date.

    Allows to filter by date range and scan job type.

    """

    def __init__(
        self,
        session: 'Session',
        start: date | None = None,
        end: date | None = None,
        type: str | None = None,
        municipality_id: 'UUID | None' = None
    ):
        self.session = session
        self.start = start or date.today()
        self.end = end or date.today()
        self.type = type
        self.municipality_id = municipality_id

    @cached_property
    def municipality_name(self) -> str | None:
        if self.municipality_id:
            query = self.session.query(Municipality.name)
            query = query.filter_by(id=self.municipality_id)
            return query.scalar()
        return None

    @cached_property
    def columns_dispatch(self) -> list[str]:
        return []

    @cached_property
    def columns_return(self) -> list[str]:
        return []

    @cached_property
    def columns(self) -> list[str]:
        return self.columns_dispatch + self.columns_return

    def query(self) -> 'Query[Any]':
        # aggregate on dispatch date
        query_in = self.session.query(ScanJob).join(Municipality)
        query_in = query_in.with_entities(
            Municipality.name.label('name'),
            Municipality.meta['bfs_number'].label('bfs_number'),
            *[sum(ScanJob, column) for column in self.columns_dispatch],
            *[zero(column) for column in self.columns_return],
        )
        query_in = query_in.filter(
            ScanJob.dispatch_date >= self.start,
            ScanJob.dispatch_date <= self.end
        )
        if self.type in ('normal', 'express'):
            query_in = query_in.filter(ScanJob.type == self.type)
        if self.municipality_id:
            query_in = query_in.filter(
                Municipality.id == self.municipality_id
            )
        query_in = query_in.group_by(
            Municipality.name,
            Municipality.meta['bfs_number'].label('bfs_number')
        )

        # aggregate on return date
        query_out = self.session.query(ScanJob).join(Municipality)
        query_out = query_out.with_entities(
            Municipality.name.label('name'),
            Municipality.meta['bfs_number'].label('bfs_number'),
            *[zero(column) for column in self.columns_dispatch],
            *[sum(ScanJob, column) for column in self.columns_return],
        )
        query_out = query_out.filter(
            ScanJob.return_date >= self.start,
            ScanJob.return_date <= self.end
        )
        if self.type in ('normal', 'express'):
            query_out = query_out.filter(ScanJob.type == self.type)
        if self.municipality_id:
            query_out = query_out.filter(
                Municipality.id == self.municipality_id
            )
        query_out = query_out.group_by(
            Municipality.name,
            Municipality.meta['bfs_number'].label('bfs_number')
        )

        # join
        union = query_in.union_all(query_out).subquery('union')
        query = self.session.query(
            union.c.name,
            union.c.bfs_number,
            *[sum(union.c, column) for column in self.columns]
        )
        query = query.group_by(union.c.name, union.c.bfs_number)
        query = query.order_by(unaccent(union.c.name))
        return query

    def total(self) -> 'Query[tuple[int, ...]]':
        subquery = self.query().subquery()
        query = self.session.query(
            *[sum(subquery.c, column) for column in self.columns],
        )
        return query.one()


class ReportBoxes(Report):
    """ A report containing all boxes from the municipalities of normal scan
    jobs. """

    def __init__(
        self,
        session: 'Session',
        start: date | None = None,
        end: date | None = None
    ):
        super().__init__(session, start, end, 'normal')

    @cached_property
    def columns_dispatch(self) -> list[str]:
        return [
            'dispatch_boxes',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
            'return_boxes'
        ]


class ReportBoxesAndForms(Report):
    """ A report containing all boxes, tax forms and single documents. """

    @cached_property
    def columns_dispatch(self) -> list[str]:
        return [
            'return_scanned_tax_forms_older',
            'return_scanned_tax_forms_last_year',
            'return_scanned_tax_forms_current_year',
            'return_scanned_tax_forms',
            'return_scanned_single_documents',
            'return_boxes'
        ]


class ReportFormsByMunicipality(Report):
    """ A report containing all tax forms of a single municipality. """

    @cached_property
    def columns_dispatch(self) -> list[str]:
        return [
            'return_scanned_tax_forms_older',
            'return_scanned_tax_forms_last_year',
            'return_scanned_tax_forms_current_year',
            'return_scanned_tax_forms',
        ]


class ReportFormsAllMunicipalities(ReportFormsByMunicipality):
    """ A report containing all tax forms of all municipalities. """

    @cached_property
    def municipality_name(self) -> str:
        return _('Report forms of all municipalities')


class ReportBoxesAndFormsByDelivery:
    """ A report containing all boxes, tax forms and single documents of a
    single municipality by delivery.

    """

    def __init__(
        self,
        session: 'Session',
        start: date,
        end: date,
        type: str,
        municipality_id: 'UUID'
    ):
        self.session = session
        self.start = start
        self.end = end
        self.type = type
        self.municipality_id = municipality_id

    @property
    def municipality(self) -> Municipality:
        query = self.session.query(Municipality)
        query = query.filter_by(id=self.municipality_id)
        return query.one()

    @cached_property
    def columns(self) -> list[str]:
        return [
            'dispatch_date',
            'delivery_number',
            'return_scanned_tax_forms_older',
            'return_scanned_tax_forms_last_year',
            'return_scanned_tax_forms_current_year',
            'return_scanned_tax_forms',
            'return_scanned_single_documents',
            'return_boxes'

        ]

    def query(self) -> 'Query[Any]':
        query = self.session.query(
            *[getattr(ScanJob, column) for column in self.columns]
        )
        query = query.filter(
            ScanJob.dispatch_date >= self.start,
            ScanJob.dispatch_date <= self.end,
            ScanJob.municipality_id == self.municipality_id
        )
        if self.type in ('normal', 'express'):
            query = query.filter(ScanJob.type == self.type)
        query = query.order_by(
            ScanJob.dispatch_date,
            ScanJob.delivery_number
        )
        return query

    def total(self) -> 'Query[tuple[int, ...]]':
        subquery = self.query().subquery()
        query = self.session.query(
            zero('dispatch_date'),
            zero('delivery_number'),
            *[sum(subquery.c, column) for column in self.columns[2:]],
        )
        return query.one()
