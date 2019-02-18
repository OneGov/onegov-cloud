from datetime import date
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import ScanJob
from sqlalchemy import func
from sqlalchemy.sql.expression import literal_column


def sum(table, attribute):
    result = func.coalesce(func.sum(getattr(table, attribute)), 0)
    return result.label(attribute)


class DailyList(object):
    """ A tax form scan job date. """

    types = {'boxes', 'forms'}

    def __init__(self, session, type_=None, date_=None):
        self.session = session
        self.type = type_ if type_ in self.types else 'boxes'
        self.date = date_ or date.today()

    @property
    def jobs(self):
        query_in = self.session.query(ScanJob).join(Municipality)
        query_in = query_in.with_entities(
            Municipality.name.label('name'),
            sum(ScanJob, 'dispatch_boxes'),
            sum(ScanJob, 'dispatch_cantonal_tax_office'),
            sum(ScanJob, 'dispatch_cantonal_scan_center'),
            literal_column('0').label('return_boxes')
        )
        query_in = query_in.filter(ScanJob.dispatch_date == self.date)
        query_in = query_in.group_by(Municipality.name)
        query_in = query_in.order_by(Municipality.name)

        query_out = self.session.query(ScanJob).join(Municipality)
        query_out = query_out.with_entities(
            Municipality.name.label('name'),
            literal_column('0').label('dispatch_boxes'),
            literal_column('0').label('dispatch_cantonal_tax_office'),
            literal_column('0').label('dispatch_cantonal_scan_center'),
            sum(ScanJob, 'return_boxes'),
        )
        query_out = query_out.filter(ScanJob.return_date == self.date)
        query_out = query_out.group_by(Municipality.name)
        query_out = query_out.order_by(Municipality.name)

        union = query_in.union_all(query_out).subquery('union')
        query = self.session.query(
            union.c.name,
            sum(union.c, 'dispatch_boxes'),
            sum(union.c, 'dispatch_cantonal_tax_office'),
            sum(union.c, 'dispatch_cantonal_scan_center'),
            sum(union.c, 'return_boxes'),
        )
        query = query.group_by(union.c.name)
        query = query.order_by(union.c.name)
        return query

    @property
    def total(self):
        jobs = self.jobs.subquery()
        query = self.session.query(
            sum(jobs.c, 'dispatch_boxes'),
            sum(jobs.c, 'dispatch_cantonal_tax_office'),
            sum(jobs.c, 'dispatch_cantonal_scan_center'),
            sum(jobs.c, 'return_boxes'),
        )
        return query.one()
