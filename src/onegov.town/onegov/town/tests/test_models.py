import os
import pytz

from datetime import datetime, date
from freezegun import freeze_time
from io import BytesIO
from onegov.core.request import CoreRequest
from onegov.core.utils import module_path, rchop
from onegov.page import PageCollection
from onegov.testing import utils
from onegov.town.models import (
    Clipboard,
    FileCollection,
    ImageCollection,
    SiteCollection
)
from onegov.town.models.resource import SharedMethods
from unittest.mock import Mock, patch


def test_file_collection(town_app):

    collection = FileCollection(town_app)
    assert list(collection.files) == []
    assert collection.get_file_by_filename('b.txt') is None

    collection.store_file(BytesIO(b'test'), 'b.txt')
    assert len(list(collection.files)) == 1
    assert collection.get_file_by_filename('b.txt') is not None

    collection.store_file(BytesIO(b'test'), 'a.txt')
    assert len(list(collection.files)) == 2
    assert collection.get_file_by_filename('a.txt') is not None
    assert [f.filename for f in collection.files] == ['a.txt', 'b.txt']

    collection.delete_file_by_filename('a.txt')
    collection.delete_file_by_filename('b.txt')
    assert len(list(collection.files)) == 0
    assert collection.get_file_by_filename('a.txt') is None
    assert collection.get_file_by_filename('b.txt') is None


def test_image_collection(town_app):

    collection = ImageCollection(town_app)
    assert list(collection.files) == []
    assert list(collection.thumbnails) == []

    assert collection.get_file_by_filename('test.jpg') is None
    collection.store_file(utils.create_image(), 'test.jpg')
    assert collection.get_file_by_filename('test.jpg') is not None

    assert len(list(collection.files)) == 1
    assert len(list(collection.thumbnails)) == 0

    assert collection.get_thumbnail_by_filename('test.jpg') is not None

    assert len(list(collection.files)) == 1
    assert len(list(collection.thumbnails)) == 1

    collection.delete_file_by_filename('test.jpg')

    assert len(list(collection.files)) == 0
    assert len(list(collection.thumbnails)) == 0


def test_clipboard(town_app):

    request = CoreRequest(environ={
        'PATH_INFO': '/',
        'SERVER_NAME': '',
        'SERVER_PORT': '',
        'SERVER_PROTOCOL': 'https'
    }, app=town_app)

    clipboard = Clipboard.from_url(request, 'https://google.ch')
    assert clipboard.url == 'https://google.ch'

    clipboard.store_in_session()
    assert clipboard.from_session(clipboard.request).url == 'https://google.ch'

    clipboard.clear()
    assert clipboard.from_session(clipboard.request).url is None

    clipboard = Clipboard(request, clipboard.token + 'x')
    assert clipboard.url is None


def test_sitecollection(town_app):

    sitecollection = SiteCollection(town_app.session())
    objects = sitecollection.get()

    assert {o.name for o in objects['topics']} == {
        'leben-wohnen',
        'kultur-freizeit',
        'bildung-gesellschaft',
        'gewerbe-tourismus',
        'politik-verwaltung'
    }

    assert {o.name for o in objects['news']} == {
        'aktuelles',
        'willkommen-bei-onegov'
    }

    paths = (p for p in os.listdir(module_path('onegov.town', 'forms')))
    paths = (p for p in paths if p.endswith('.form'))
    paths = (os.path.basename(p) for p in paths)
    builtin_forms = set(rchop(p, '.form') for p in paths)

    assert {o.name for o in objects['forms']} == set(builtin_forms)

    assert {o.name for o in objects['resources']} == {'sbb-tageskarte'}


def test_news_years(town_app):

    collection = PageCollection(town_app.session())
    news = collection.add_root("News", type='news')
    one = collection.add(news, title="One", type='news')
    two = collection.add(news, title="Two", type='news')

    assert news.years == [datetime.utcnow().year]

    one.created = datetime(2016, 2, 1, tzinfo=pytz.utc)
    two.created = datetime(2015, 2, 1, tzinfo=pytz.utc)

    assert news.years == [2016, 2015]


def test_image_grouping(town_app):

    class MockImage(object):
        def __init__(self, mod_time):
            self.info = {'modified_time': mod_time}

    with patch('onegov.town.models.ImageCollection.files') as files:
        today = date(2008, 8, 8)

        images = [
            MockImage(datetime(2008, 9, 1, 16, 00)),  # (next month)
            MockImage(datetime(2008, 8, 3, 16, 00)),  # this month
            MockImage(datetime(2008, 8, 2, 16, 00)),  # this month
            MockImage(datetime(2008, 8, 1, 0, 00)),  # this month
            MockImage(datetime(2008, 7, 1, 16, 00)),  # last month
            MockImage(datetime(2008, 5, 1, 16, 00)),  # this year
            MockImage(datetime(2008, 2, 4, 12, 00)),  # this year
            MockImage(datetime(2007, 12, 1, 16, 00)),  # last year
            MockImage(datetime(2007, 10, 2, 14, 00)),  # last year
            MockImage(datetime(2005, 4, 1, 16, 00)),  # older
            MockImage(datetime(2002, 6, 4, 16, 00)),  # older
        ]
        files.__get__ = Mock(return_value=images)

        groups = ImageCollection(town_app).grouped_files(today=today)
        assert groups[0][0] == 'This month'
        assert groups[0][1] == images[0:4]
        assert groups[1][0] == 'Last month'
        assert groups[1][1] == images[4:5]
        assert groups[2][0] == 'This year'
        assert groups[2][1] == images[5:7]
        assert groups[3][0] == 'Last year'
        assert groups[3][1] == images[7:9]
        assert groups[4][0] == 'Older'
        assert groups[4][1] == images[9:]

    with patch('onegov.town.models.ImageCollection.files') as files:
        today = date(2008, 8, 8)

        images = [
            MockImage(datetime(2008, 8, 3, 16, 00)),  # this month
            MockImage(datetime(2008, 5, 1, 16, 00)),  # this year
            MockImage(datetime(2002, 6, 4, 16, 00)),  # older
        ]
        files.__get__ = Mock(return_value=images)

        groups = ImageCollection(town_app).grouped_files(today=today)
        assert groups[0][0] == 'This month'
        assert groups[0][1] == images[0:1]
        assert groups[1][0] == 'This year'
        assert groups[1][1] == images[1:2]
        assert groups[2][0] == 'Older'
        assert groups[2][1] == images[2:]

    with patch('onegov.town.models.ImageCollection.files') as files:
        today = date(2008, 8, 8)

        images = [
            MockImage(datetime(2008, 7, 1, 16, 00)),  # last month
            MockImage(datetime(2002, 6, 4, 16, 00)),  # older
        ]
        files.__get__ = Mock(return_value=images)

        groups = ImageCollection(town_app).grouped_files(today=today)
        assert groups[0][0] == 'Last month'
        assert groups[0][1] == images[0:1]
        assert groups[1][0] == 'Older'
        assert groups[1][1] == images[1:]

    with patch('onegov.town.models.ImageCollection.files') as files:
        today = date(2008, 8, 8)

        images = [
            MockImage(datetime(2008, 8, 1, 0, 00)),  # this month
            MockImage(datetime(2008, 2, 4, 12, 00)),  # this year
        ]
        files.__get__ = Mock(return_value=images)

        groups = ImageCollection(town_app).grouped_files(today=today)
        assert groups[0][0] == 'This month'
        assert groups[0][1] == images[0:1]
        assert groups[1][0] == 'This year'
        assert groups[1][1] == images[1:]

    with patch('onegov.town.models.ImageCollection.files') as files:
        today = date(2008, 8, 8)

        images = [
            MockImage(datetime(2008, 8, 1, 0, 00)),  # this month
        ]
        files.__get__ = Mock(return_value=images)

        groups = ImageCollection(town_app).grouped_files(today=today)
        assert groups[0][0] == 'This month'
        assert groups[0][1] == images[0:1]

    with patch('onegov.town.models.ImageCollection.files') as files:
        today = date(2008, 8, 8)

        images = [
            MockImage(datetime(2008, 7, 1, 0, 00)),  # last month
        ]
        files.__get__ = Mock(return_value=images)

        groups = ImageCollection(town_app).grouped_files(today=today)
        assert groups[0][0] == 'Last month'
        assert groups[0][1] == images[0:1]

    with patch('onegov.town.models.ImageCollection.files') as files:
        today = date(2008, 8, 8)

        images = [
            MockImage(datetime(2002, 7, 1, 0, 00)),  # older
        ]
        files.__get__ = Mock(return_value=images)

        groups = ImageCollection(town_app).grouped_files(today=today)
        assert groups[0][0] == 'Older'
        assert groups[0][1] == images[0:1]

    with patch('onegov.town.models.ImageCollection.files') as files:
        today = date(2008, 1, 8)

        images = [
            MockImage(datetime(2008, 1, 3, 16, 00)),  # this month/year
            MockImage(datetime(2008, 1, 2, 16, 00)),  # this month/year
            MockImage(datetime(2008, 1, 1, 0, 00)),  # this month/year
            MockImage(datetime(2007, 12, 14, 16, 00)),  # last month/year
            MockImage(datetime(2007, 12, 12, 16, 00)),  # last month/year
            MockImage(datetime(2007, 10, 2, 14, 00)),  # last year
            MockImage(datetime(2002, 6, 4, 16, 00)),  # older
        ]
        files.__get__ = Mock(return_value=images)

        groups = ImageCollection(town_app).grouped_files(today=today)
        assert groups[0][0] == 'This month'
        assert groups[0][1] == images[0:3]
        assert groups[1][0] == 'Last month'
        assert groups[1][1] == images[3:5]
        assert groups[2][0] == 'Last year'
        assert groups[2][1] == images[5:6]
        assert groups[3][0] == 'Older'
        assert groups[3][1] == images[6:]


def test_calendar_date_range():
    resource = SharedMethods()
    utc = pytz.timezone('UTC')

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
