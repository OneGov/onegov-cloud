""" Contains the models describing files and images. """

from collections import namedtuple
from datetime import datetime
from dateutil.relativedelta import relativedelta
from itertools import groupby
from onegov.core.orm.mixins import meta_property
from onegov.file import File, FileSet, FileCollection, FileSetCollection
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.org import _
from onegov.org.models.extensions import HiddenFromPublicExtension
from onegov.search import ORMSearchable
from sedate import standardize_date, utcnow
from sqlalchemy import desc


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

    def query_intervals(self, intervals, before_filter=None, process=None):
        base_query = self.query().order_by(desc(File.last_change))

        if before_filter:
            base_query = before_filter(base_query)

        for interval in intervals:
            query = base_query.filter(File.last_change >= interval.start)
            query = query.filter(File.last_change <= interval.end)

            for result in query.all():
                if process is not None:
                    yield interval.name, process(result)

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

        def process(result):
            if id_only:
                return result.id

            return result

        return groupby(
            self.query_intervals(intervals, before_filter, process),
            key=lambda item: item[0]
        )


class GeneralFile(File):
    __mapper_args__ = {'polymorphic_identity': 'general'}


class ImageFile(File):
    __mapper_args__ = {'polymorphic_identity': 'image'}


class ImageSet(FileSet, HiddenFromPublicExtension, ORMSearchable):
    __mapper_args__ = {'polymorphic_identity': 'image'}

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'}
    }

    @property
    def es_public(self):
        return not self.is_hidden_from_public

    @property
    def es_language(self):
        return 'de'  # xxx for now there's no other language

    @property
    def es_suggestions(self):
        return {
            "input": [self.title.lower()]
        }

    lead = meta_property('lead')
    view = meta_property('view')

    show_images_on_homepage = meta_property('show_images_on_homepage')


class ImageSetCollection(FileSetCollection):

    def __init__(self, session):
        super().__init__(session, type='image')


class GeneralFileCollection(FileCollection, GroupFilesByDateMixin):

    supported_content_types = 'all'

    def __init__(self, session):
        super().__init__(session, type='general', allow_duplicates=False)


class ImageFileCollection(FileCollection, GroupFilesByDateMixin):

    supported_content_types = IMAGE_MIME_TYPES_AND_SVG

    def __init__(self, session):
        super().__init__(session, type='image', allow_duplicates=False)
