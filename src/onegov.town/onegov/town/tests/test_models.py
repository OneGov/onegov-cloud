from datetime import datetime, date
from dateutil import relativedelta
from mock import Mock, patch
from onegov.testing import utils
from onegov.town.models import ImageCollection


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
        assert groups[1][0] == 'Older'
        assert groups[1][1] == images[1:]

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
