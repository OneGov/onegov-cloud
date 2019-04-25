import re

from base64 import b64encode, b64decode
from onegov.core.custom import json
from onegov.form import Form
from onegov.gis.models import Coordinates
from onegov.gis.forms import CoordinatesField


def test_coordinates_field():
    value = re.compile(r'value="([a-zA-Z0-9=]+)"')

    # initially the field contains empty coordinates
    field = CoordinatesField().bind(Form(), 'coordinates')
    assert not field.data
    assert field.data.lat is None
    assert field.data.lon is None
    assert field.data.zoom is None

    # this holds true for the rendered field
    coordinate = json.loads(b64decode(value.search(field()).group(1)))

    assert coordinate.lat is None
    assert coordinate.lon is None
    assert coordinate.zoom is None

    # when we process a dictionary we get non-empty coordinates
    field.process_formdata([b64encode(
        json.dumps({
            'lat': 47.05183585,
            'lon': 8.30576869173879,
            'zoom': 10
        }).encode('ascii')
    ).decode('ascii')])

    assert field.data.lat == 47.05183585
    assert field.data.lon == 8.30576869173879
    assert field.data.zoom == 10

    # which again holds true for the rendered field
    coordinate = json.loads(b64decode(value.search(field()).group(1)))

    assert coordinate.lat == 47.05183585
    assert coordinate.lon == 8.30576869173879
    assert coordinate.zoom == 10

    # when we process a dictionary coordinates are created
    field.process_data({
        'lat': 47.05183585,
        'lon': 8.30576869173879,
        'zoom': None
    })

    assert field.data.lat == 47.05183585
    assert field.data.lon == 8.30576869173879
    assert field.data.zoom is None

    # on an object, coordinates are stored as is
    class Test(object):
        pass

    test = Test()
    field.populate_obj(test, 'coordinates')

    assert test.coordinates.lat == 47.05183585
    assert test.coordinates.lon == 8.30576869173879

    field.data = Coordinates()
    field.populate_obj(test, 'coordinates')
    assert test.coordinates.lat is None
    assert test.coordinates.lon is None
    assert test.coordinates.zoom is None
