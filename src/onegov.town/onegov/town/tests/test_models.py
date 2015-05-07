from onegov.testing import utils
from onegov.town.models import ImageCollection


def test_image_collection(town_app):

    collection = ImageCollection(town_app)
    assert list(collection.images) == []
    assert list(collection.thumbnails) == []

    assert collection.get_image_by_filename('test.jpg') is None
    collection.store_image(utils.create_image(), 'test.jpg')
    assert collection.get_image_by_filename('test.jpg') is not None

    assert len(list(collection.images)) == 1
    assert len(list(collection.thumbnails)) == 0

    assert collection.get_thumbnail_by_filename('test.jpg') is not None

    assert len(list(collection.images)) == 1
    assert len(list(collection.thumbnails)) == 1

    collection.delete_image_by_filename('test.jpg')

    assert len(list(collection.images)) == 0
    assert len(list(collection.thumbnails)) == 0
