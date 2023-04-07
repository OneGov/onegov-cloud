import os

from collections import OrderedDict
from datetime import datetime, date
from freezegun import freeze_time
from onegov.core.request import CoreRequest
from onegov.core.utils import module_path, rchop
from onegov.org.models import Clipboard, ImageFileCollection
from onegov.org.models import Organisation
from onegov.org.models import SiteCollection
from onegov.org.models.file import GroupFilesByDateMixin
from onegov.org.models.resource import SharedMethods
from onegov.page import PageCollection
from tests.shared.utils import create_image
from pytz import utc


def test_clipboard(org_app):

    request = CoreRequest(environ={
        'PATH_INFO': '/',
        'SERVER_NAME': '',
        'SERVER_PORT': '',
        'SERVER_PROTOCOL': 'https'
    }, app=org_app)

    clipboard = Clipboard.from_url(request, 'https://google.ch')
    assert clipboard.url == 'https://google.ch'

    clipboard.store_in_session()
    assert clipboard.from_session(clipboard.request).url == 'https://google.ch'

    clipboard.clear()
    assert clipboard.from_session(clipboard.request).url is None

    clipboard = Clipboard(request, clipboard.token + 'x')
    assert clipboard.url is None


def test_news(session):

    collection = PageCollection(session)
    news = collection.add_root("News", type='news')
    one = collection.add(
        news,
        title='One',
        type='news',
        lead='#one #both',
    )
    one.created = datetime(2016, 1, 1, tzinfo=utc)
    two = collection.add(
        news,
        title='Two',
        type='news',
        text='#two #both'
    )
    two.created = datetime(2015, 3, 1, tzinfo=utc)
    three = collection.add(
        news,
        title='Three',
        type='news',
        text='#three'
    )
    three.created = datetime(2015, 2, 1, tzinfo=utc)
    three.publication_start = datetime(2015, 2, 2, tzinfo=utc)
    three.publication_end = datetime(2015, 2, 4, tzinfo=utc)
    four = collection.add(
        news,
        title='Four',
        type='news',
        text='#four'
    )
    four.created = datetime(2015, 1, 1, tzinfo=utc)
    four.is_visible_on_homepage = True

    assert news.all_years == [2016, 2015]
    assert news.all_tags == ['both', 'four', 'one', 'three', 'two']

    assert news.for_year(2015).filter_years == [2015]
    assert news.for_year(2015).filter_tags == []
    assert news.for_tag('one').filter_years == []
    assert news.for_tag('one').filter_tags == ['one']
    news.filter_years = [2015]
    news.filter_tags = ['one']
    assert news.for_year(2015).filter_years == []
    assert news.for_year(2015).filter_tags == ['one']
    assert news.for_tag('one').filter_years == [2015]
    assert news.for_tag('one').filter_tags == []
    assert news.for_year(2016).filter_years == [2015, 2016]
    assert news.for_year(2016).filter_tags == ['one']
    assert news.for_tag('two').filter_years == [2015]
    assert news.for_tag('two').filter_tags == ['one', 'two']

    news.filter_years = []
    news.filter_tags = []
    assert news.news_query(limit=None, published_only=False).count() == 4
    assert news.news_query(limit=None, published_only=True).count() == 3
    assert news.news_query(limit=0, published_only=True).count() == 1
    assert news.news_query(limit=1, published_only=True).count() == 2
    assert news.news_query(limit=2, published_only=True).count() == 3
    assert news.news_query(limit=3, published_only=True).count() == 3

    news.filter_years = [2016]
    assert news.news_query(limit=None, published_only=False).count() == 1
    news.filter_years = [2015]
    assert news.news_query(limit=None, published_only=False).count() == 3
    news.filter_years = [2015, 2016]
    assert news.news_query(limit=None, published_only=False).count() == 4

    news.filter_tags = ['one']
    assert news.news_query(limit=None, published_only=False).count() == 1
    news.filter_tags = ['both']
    assert news.news_query(limit=None, published_only=False).count() == 2
    news.filter_tags = ['both', 'three']
    assert news.news_query(limit=None, published_only=False).count() == 3

    news.filter_years = [2015]
    news.filter_tags = ['both']
    assert news.news_query(limit=None, published_only=False).one() == two


def test_group_intervals():
    mixin = GroupFilesByDateMixin()

    intervals = list(mixin.get_date_intervals(datetime(2016, 1, 1)))

    assert intervals[0].name == 'This month'
    assert intervals[0].start.date() == date(2016, 1, 1)
    assert intervals[0].end.date() == date(2016, 1, 31)

    assert intervals[1].name == 'Last month'
    assert intervals[1].start.date() == date(2015, 12, 1)
    assert intervals[1].end.date() == date(2015, 12, 31)

    assert intervals[2].name == 'Last year'
    assert intervals[2].start.date() == date(2015, 1, 1)
    assert intervals[2].end.date() == date(2015, 11, 30)

    assert intervals[3].name == 'Older'
    assert intervals[3].start.date() == date(2000, 1, 1)
    assert intervals[3].end.date() == date(2014, 12, 31)

    intervals = list(mixin.get_date_intervals(datetime(2016, 2, 1)))

    assert intervals[0].name == 'This month'
    assert intervals[0].start.date() == date(2016, 2, 1)
    assert intervals[0].end.date() == date(2016, 2, 29)

    assert intervals[1].name == 'Last month'
    assert intervals[1].start.date() == date(2016, 1, 1)
    assert intervals[1].end.date() == date(2016, 1, 31)

    assert intervals[2].name == 'Last year'
    assert intervals[2].start.date() == date(2015, 1, 1)
    assert intervals[2].end.date() == date(2015, 12, 31)

    assert intervals[3].name == 'Older'
    assert intervals[3].start.date() == date(2000, 1, 1)
    assert intervals[3].end.date() == date(2014, 12, 31)

    intervals = list(mixin.get_date_intervals(datetime(2016, 3, 1)))

    assert intervals[0].name == 'This month'
    assert intervals[0].start.date() == date(2016, 3, 1)
    assert intervals[0].end.date() == date(2016, 3, 31)

    assert intervals[1].name == 'Last month'
    assert intervals[1].start.date() == date(2016, 2, 1)
    assert intervals[1].end.date() == date(2016, 2, 29)

    assert intervals[2].name == 'This year'
    assert intervals[2].start.date() == date(2016, 1, 1)
    assert intervals[2].end.date() == date(2016, 1, 31)

    assert intervals[3].name == 'Last year'
    assert intervals[3].start.date() == date(2015, 1, 1)
    assert intervals[3].end.date() == date(2015, 12, 31)

    assert intervals[4].name == 'Older'
    assert intervals[4].start.date() == date(2000, 1, 1)
    assert intervals[4].end.date() == date(2014, 12, 31)


def test_image_grouping(session):

    collection = ImageFileCollection(session)

    def grouped_by_date(today):
        grouped = collection.grouped_by_date(today=today)
        return OrderedDict((g, [i[1] for i in items]) for g, items in grouped)

    def delete(images):
        for image in images:
            collection.delete(image)

    # catches all intervals
    images = [collection.add('x.png', create_image()) for r in range(0, 11)]
    images[0].created = datetime(2008, 9, 1, 16, 0, tzinfo=utc)   # next month
    images[1].created = datetime(2008, 8, 3, 16, 0, tzinfo=utc)   # this month
    images[2].created = datetime(2008, 8, 2, 16, 0, tzinfo=utc)   # this month
    images[3].created = datetime(2008, 8, 1, 0, 0, tzinfo=utc)    # this month
    images[4].created = datetime(2008, 7, 1, 16, 0, tzinfo=utc)   # last month
    images[5].created = datetime(2008, 5, 1, 16, 0, tzinfo=utc)   # this year
    images[6].created = datetime(2008, 2, 4, 12, 0, tzinfo=utc)   # this year
    images[7].created = datetime(2007, 12, 1, 16, 0, tzinfo=utc)  # last year
    images[8].created = datetime(2007, 10, 2, 14, 0, tzinfo=utc)  # last year
    images[9].created = datetime(2005, 4, 1, 16, 0, tzinfo=utc)   # older
    images[10].created = datetime(2002, 6, 4, 16, 0, tzinfo=utc)  # older

    grouped = grouped_by_date(datetime(2008, 8, 8))

    assert grouped['This month'] == [img.id for img in images[1:4]]
    assert grouped['Last month'] == [img.id for img in images[4:5]]
    assert grouped['This year'] == [img.id for img in images[5:7]]
    assert grouped['Last year'] == [img.id for img in images[7:9]]
    assert grouped['Older'] == [img.id for img in images[9:]]

    delete(images)

    # only catch some intervals
    images = [collection.add('x.png', create_image()) for r in range(0, 3)]
    images[0].created = datetime(2008, 8, 3, 16, 0, tzinfo=utc)  # this month
    images[1].created = datetime(2008, 5, 1, 16, 0, tzinfo=utc)  # this year
    images[2].created = datetime(2002, 6, 4, 16, 0, tzinfo=utc)  # older

    grouped = grouped_by_date(datetime(2008, 8, 8))
    assert grouped['This month'] == [img.id for img in images[0:1]]
    assert grouped['This year'] == [img.id for img in images[1:2]]
    assert grouped['Older'] == [img.id for img in images[2:]]

    delete(images)

    # catch a different set of intervals
    images = [collection.add('x.png', create_image()) for r in range(0, 2)]
    images[0].created = datetime(2008, 7, 1, 16, 0, tzinfo=utc)  # last month
    images[1].created = datetime(2002, 6, 4, 16, 0, tzinfo=utc)  # older

    grouped = grouped_by_date(datetime(2008, 8, 8))
    assert grouped['Last month'] == [img.id for img in images[0:1]]
    assert grouped['Older'] == [img.id for img in images[1:]]

    delete(images)

    # use a different date and catch a reduced set of intervals
    images = [collection.add('x.png', create_image()) for r in range(0, 7)]
    images[0].created = datetime(2008, 1, 3, 16, 0, tzinfo=utc)   # this month
    images[1].created = datetime(2008, 1, 2, 16, 0, tzinfo=utc)   # this month
    images[2].created = datetime(2008, 1, 1, 0, 0, tzinfo=utc)    # this month
    images[3].created = datetime(2007, 12, 14, 16, 0, tzinfo=utc)  # lst month
    images[4].created = datetime(2007, 12, 12, 16, 0, tzinfo=utc)  # lst month
    images[5].created = datetime(2007, 10, 2, 14, 0, tzinfo=utc)  # last year
    images[6].created = datetime(2002, 6, 4, 16, 0, tzinfo=utc)   # older

    grouped = grouped_by_date(datetime(2008, 1, 8))
    assert grouped['This month'] == [img.id for img in images[0:3]]
    assert grouped['Last month'] == [img.id for img in images[3:5]]
    assert grouped['Last year'] == [img.id for img in images[5:6]]
    assert grouped['Older'] == [img.id for img in images[6:]]

    delete(images)


def test_calendar_date_range():
    resource = SharedMethods()

    resource.date = None
    resource.timezone = utc

    resource.view = 'month'
    with freeze_time(datetime(2016, 5, 14, tzinfo=utc)):
        assert resource.calendar_date_range == (
            datetime(2016, 5, 1, tzinfo=utc),
            datetime(2016, 5, 31, 23, 59, 59, 999999, tzinfo=utc)
        )

    resource.date = date(2016, 5, 14)
    assert resource.calendar_date_range == (
        datetime(2016, 5, 1, tzinfo=utc),
        datetime(2016, 5, 31, 23, 59, 59, 999999, tzinfo=utc)
    )

    resource.view = 'agendaWeek'
    assert resource.calendar_date_range == (
        datetime(2016, 5, 9, tzinfo=utc),
        datetime(2016, 5, 15, 23, 59, 59, 999999, tzinfo=utc)
    )

    resource.view = 'agendaDay'
    assert resource.calendar_date_range == (
        datetime(2016, 5, 14, tzinfo=utc),
        datetime(2016, 5, 14, 23, 59, 59, 999999, tzinfo=utc)
    )


def test_sitecollection(org_app):

    sitecollection = SiteCollection(org_app.session())
    objects = sitecollection.get()

    assert {o.name for o in objects['topics']} == {
        'organisation',
        'themen',
        'kontakt',
    }

    assert {o.name for o in objects['news']} == {
        'news',
        'wir-haben-eine-neue-webseite'
    }

    builtin_forms_path = module_path('onegov.org', 'forms/builtin/de')

    paths = (p for p in os.listdir(builtin_forms_path))
    paths = (p for p in paths if p.endswith('.form'))
    paths = (os.path.basename(p) for p in paths)
    builtin_forms = set(rchop(p, '.form') for p in paths)

    assert {o.name for o in objects['forms']} == set(builtin_forms)


def test_holidays():
    o = Organisation(holiday_settings={})

    assert date(2000, 1, 1) not in o.holidays
    assert date(2000, 1, 2) not in o.holidays
    assert date(2000, 1, 3) not in o.holidays

    assert len(o.holidays.all(2000)) == 0

    o.holiday_settings['cantons'] = ['AR']

    assert date(2000, 1, 1) in o.holidays
    assert date(2000, 1, 2) not in o.holidays
    assert date(2000, 1, 3) not in o.holidays

    assert len(o.holidays.all(2000)) == 8

    o.holiday_settings['cantons'] = ['AR', 'ZG']

    assert date(2000, 1, 1) in o.holidays
    assert date(2000, 1, 2) in o.holidays
    assert date(2000, 1, 3) not in o.holidays

    assert len(o.holidays.all(2000)) == 13

    o.holiday_settings['other'] = [[1, 3, 'Fooyears day']]

    assert date(2000, 1, 1) in o.holidays
    assert date(2000, 1, 2) in o.holidays
    assert date(2000, 1, 3) in o.holidays

    assert len(o.holidays.all(2000)) == 14
