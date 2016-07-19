""" Contains the models describing files and images. """

from collections import namedtuple
from datetime import datetime
from dateutil.relativedelta import relativedelta
from itertools import groupby
from onegov.file import File, FileCollection
from onegov.town import _
from sedate import standardize_date, utcnow
from sqlalchemy import desc


class GeneralFile(File):
    __mapper_args__ = {'polymorphic_identity': 'general'}


class ImageFile(File):
    __mapper_args__ = {'polymorphic_identity': 'image'}


DateInterval = namedtuple('DateInterval', ('name', 'start', 'end'))


class GroupFilesByDateMixin(object):

    def get_date_intervals(self, today):
        today = standardize_date(today, 'UTC')

        month_end = today + relativedelta(day=31)
        month_start = today - relativedelta(day=1)

        yield DateInterval(
            name=_("This month"),
            start=month_start,
            end=month_end)

        last_month_end = month_start - relativedelta(microseconds=1)
        last_month_start = month_start - relativedelta(months=1)

        yield DateInterval(
            name=_("Last month"),
            start=last_month_start,
            end=last_month_end)

        if month_start.month not in (1, 2):
            this_year_end = last_month_start - relativedelta(microseconds=1)
            this_year_start = this_year_end.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

            yield DateInterval(
                name=_("This year"),
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
            name=_("Last year"),
            start=last_year_start,
            end=last_year_end)

        older_end = last_year_start - relativedelta(microseconds=1)
        older_start = datetime(2000, 1, 1, tzinfo=today.tzinfo)

        yield DateInterval(
            name=_("Older"),
            start=older_start,
            end=older_end)

    def query_intervals(self, intervals, before_filter=None):
        base_query = self.query().order_by(desc(File.last_change))

        if before_filter:
            base_query = before_filter(base_query)

        for interval in intervals:
            query = base_query.filter(File.last_change >= interval.start)
            query = query.filter(File.last_change <= interval.end)

            for result in query.all():
                yield interval.name, result.id

    def grouped_by_date(self, today=None, id_only=True):
        """ Returns all files grouped by natural language dates.

        By default, only ids are returned, as this is enough to build the
        necessary links, which is what you usually want from a file.

        The given date is expected to be in UTC.

        """

        intervals = tuple(self.get_date_intervals(today or utcnow()))

        def before_filter(query):
            if id_only:
                return query.with_entities(File.id)

            return query

        return groupby(
            self.query_intervals(intervals, before_filter),
            key=lambda item: item[0]
        )


class GeneralFileCollection(FileCollection, GroupFilesByDateMixin):

    def __init__(self, session):
        super().__init__(session, 'general')


class ImageFileCollection(FileCollection, GroupFilesByDateMixin):

    def __init__(self, session):
        super().__init__(session, 'image')
