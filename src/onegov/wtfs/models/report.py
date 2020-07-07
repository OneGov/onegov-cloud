from collections import namedtuple
from copy import deepcopy
from itertools import groupby, chain

from cached_property import cached_property
from datetime import date
from onegov.core.orm.func import unaccent
from onegov.wtfs import _
from onegov.wtfs.models.municipality import Municipality
from onegov.wtfs.models.scan_job import ScanJob
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy.sql.expression import literal_column


def sum(table, attribute):
    result = func.coalesce(func.sum(getattr(table, attribute)), 0)
    result = func.cast(result, Integer)
    return result.label(attribute)


def zero(attribute):
    return literal_column('0').label(attribute)


def exclude(col, parts=None):
    if not parts:
        return
    for part in parts:
        if part in col:
            return part


class TransformedMixin:

    transformed_suffix = '_by_year'
    transform_entry_exclude = None

    @property
    def years(self):
        return range(self.start.year, self.end.year + 1)

    @cached_property
    def transform_added_cols(self):
        cols = []
        for col in self.columns:
            for id_ in self.transformable_col_ids:
                if id_ in col:
                    new_col = col.replace(id_, self.transformed_suffix, 1)
                    if new_col not in cols:
                        cols.append(new_col)
        return cols

    @property
    def transformable_col_ids(self):
        return '_older', '_current_year', '_last_year'

    @staticmethod
    def year_key(col, year):
        year = int(year)
        if '_last_year' in col:
            return str(year - 1)
        if '_older' in col:
            return f"older_{year - 2}"
        if 'current_year' in col:
            return str(year)

    @cached_property
    def year_dict(self):
        by_year_keys = (self.year_key('_older', year) for year in self.years)
        simple_years = range(self.years[0] - 1, self.years[-1] + 1)
        return {
            k: 0 for k in chain(
                by_year_keys,
                (str(y) for y in simple_years)
            )}

    @cached_property
    def do_transform_query(self):
        return self.transform_added_cols and True or False

    def transformed_entry(self, excluded=None):
        first = self.query().first()
        excluded = excluded or []
        if not first:
            return None
        ignored = [
            col for col in first._fields if self.year_key(col, 10)] + excluded

        if not ignored:
            return namedtuple('TransformedEntry', first._fields)
        return namedtuple('TransformedEntry', chain(
            (col for col in first._fields if col not in ignored),
            self.transform_added_cols
        ))

    def _replace(self, col):
        to_replace = exclude(col, self.transformable_col_ids)
        if to_replace:
            return col.replace(to_replace, self.transformed_suffix, 1)
        return col

    def transform(self, query, exclude_cols=None):
        """Since the report can span over more than a year, adding up the
        database columns get's messy in sql. This is a wrapper to enrich
        the query results and return a new namedtuple.

        if any of the returned columns contain one of the `id_parts`,
        a new key is added with the `id_part` replaced by `_by_year`.
        """

        first = query.first()
        if not first:
            return []

        all_cols = first._fields
        sum_cols = self.columns
        normal_cols = set(all_cols) - set(sum_cols) - set(exclude_cols or [])

        def add_up(results):
            """ Adds up the results correctly, imitating sum with a group_py by
            bfs_number only for columns which do not have to be summed relative
            to the return_date. """
            store = {}
            for result in results:
                for col in all_cols:
                    if exclude(col, self.transformable_col_ids):
                        current = store.setdefault(
                            self._replace(col), deepcopy(self.year_dict))
                        current[self.year_key(col, result.year)] += getattr(
                            result, col)
                    elif col in sum_cols:
                        store.setdefault(col, 0)
                        store[col] += getattr(result, col) or 0
                    elif col in normal_cols:
                        if col not in store:
                            store[col] = getattr(result, col) or 0
                    else:
                        raise NotImplementedError
            return store

        return [
            self.transformed_entry()(**add_up(res)) for bfsnr, res in groupby(
                query, key=lambda e: e.bfs_number)
        ]

    def query_results(self):
        return self.transform(self.query())

    def query_total(self, excluded=None):
        excluded = excluded or []
        results = self.query_results()
        if not results:
            return self.total()
        sums = {}
        for result in results:
            for col in result._fields:
                if col in excluded:
                    continue
                if col in self.columns:
                    sums.setdefault(col, 0)
                    sums[col] += getattr(result, col) or 0
                if col in self.transform_added_cols:
                    dict_ = getattr(result, col)
                    stored = sums.setdefault(col, self.year_dict)
                    for k, v in dict_.items():
                        stored.setdefault(k, 0)
                        stored[k] += v or 0

        return namedtuple('TransformedEntry', sums.keys())(**sums)


class Report(TransformedMixin):
    """ The base class for the reports.

    Aggregates the ``columns_dispatch`` on the dispatch date and
    ``columns_return`` on the return date.

    Allows to filter by date range and scan job type.

    """

    def __init__(
        self, session, start=None, end=None, type=None, municipality_id=None
    ):
        self.session = session
        self.start = start or date.today()
        self.end = end or date.today()
        self.type = type
        self.municipality_id = municipality_id

    @cached_property
    def municipality_name(self):
        if self.municipality_id:
            query = self.session.query(Municipality.name)
            query = query.filter_by(id=self.municipality_id)
            return query.scalar()

    @cached_property
    def columns_dispatch(self):
        return []

    @cached_property
    def columns_return(self):
        return []

    @cached_property
    def columns(self):
        return self.columns_dispatch + self.columns_return

    def query(self):
        query_in = self.session.query(ScanJob).join(Municipality)

        default_entities = [
            Municipality.name.label('name'),
            Municipality.meta['bfs_number'].label('bfs_number')
        ]
        if self.do_transform_query:
            default_entities.append(ScanJob.year)

        query_in = query_in.with_entities(
            *default_entities,
            *[sum(ScanJob, column) for column in self.columns_dispatch],
            *[zero(column) for column in self.columns_return],
        )
        if self.type in ('normal', 'express'):
            query_in = query_in.filter(ScanJob.type == self.type)
        if self.municipality_id:
            query_in = query_in.filter(
                Municipality.id == self.municipality_id
            )
        query_in = query_in.filter(
            ScanJob.dispatch_date >= self.start,
            ScanJob.dispatch_date <= self.end
        )
        query_in = query_in.group_by(*default_entities)

        # aggregate on return date
        query_out = self.session.query(ScanJob).join(Municipality)
        query_out = query_out.with_entities(
            *default_entities,
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

        query_out = query_out.group_by(*default_entities)

        # join
        union = query_in.union_all(query_out).subquery('union')
        union_entities = [union.c.name, union.c.bfs_number]
        if self.do_transform_query:
            union_entities.append(union.c.year)
        query = self.session.query(
            *union_entities,
            *[sum(union.c, column) for column in self.columns]
        )
        query = query.group_by(*union_entities,)
        final_ordering = [unaccent(union.c.name)]
        if self.do_transform_query:
            final_ordering.append(union.c.year)
        query = query.order_by(*final_ordering)
        return query

    def total(self):
        subquery = self.query().subquery()
        query = self.session.query(
            *[sum(subquery.c, column) for column in self.columns],
        )
        return query.one()

    @property
    def years(self):
        return tuple(range(self.start.year, self.end.year + 1))


class ReportBoxes(Report):
    """ A report containing all boxes from the municipalities of normal scan
    jobs. """

    def __init__(self, session, start=None, end=None):
        super().__init__(session, start, end, 'normal')

    @cached_property
    def columns_dispatch(self):
        return [
            'dispatch_boxes',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
            'return_boxes'
        ]


class ReportBoxesAndForms(Report):
    """ A report containing all boxes, tax forms and single documents. """

    @cached_property
    def columns_dispatch(self):
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
    def columns_dispatch(self):
        return [
            'return_scanned_tax_forms_older',
            'return_scanned_tax_forms_last_year',
            'return_scanned_tax_forms_current_year',
            'return_scanned_tax_forms',
        ]


class ReportFormsAllMunicipalities(ReportFormsByMunicipality):
    """ A report containing all tax forms of all municipalities. """

    @cached_property
    def municipality_name(self):
        return _("Report forms of all municipalities")


class ReportBoxesAndFormsByDelivery(TransformedMixin):
    """ A report containing all boxes, tax forms and single documents of a
    single municipality by delivery.

    """

    def __init__(self, session, start, end, type, municipality_id):
        self.session = session
        self.start = start
        self.end = end
        self.type = type
        self.municipality_id = municipality_id

    @property
    def municipality(self):
        query = self.session.query(Municipality)
        query = query.filter_by(id=self.municipality_id)
        return query.one()

    @cached_property
    def columns(self):
        return (
            'dispatch_date',
            'delivery_number',
            'return_scanned_tax_forms_older',
            'return_scanned_tax_forms_last_year',
            'return_scanned_tax_forms_current_year',
            'return_scanned_tax_forms',
            'return_scanned_single_documents',
            'return_boxes'
        )

    def query(self):
        query = self.session.query(
            *[getattr(ScanJob, column) for column in self.columns],
            ScanJob.year,
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

    def query_results(self, exclude_cols=None):
        exclude_cols = exclude_cols or []
        results = []
        for result in self.query():
            store = {}
            for col in result._fields:
                if col in exclude_cols:
                    continue
                if exclude(col, self.transformable_col_ids):
                    current = store.setdefault(
                        self._replace(col), deepcopy(self.year_dict))
                    current[self.year_key(col, result.year)] = getattr(
                        result, col)
                else:
                    store[col] = getattr(result, col)
            results.append(self.transformed_entry(exclude_cols)(**store))
        return results

    # def total(self):
    #     # fallback if query results are none
    #     excluded = ['year', 'dispatch_date', 'delivery_number']
    #     cols = set(self.columns) - set(excluded) + self.tra
    #
    #     return self.transformed_entry(excluded)

    def query_total(self):
        if not self.query_results():
            return
        return super().query_total(
            excluded=('year', 'dispatch_date', 'delivery_number'))
