import json

from base64 import b64encode
from onegov.form import Form
from onegov.gis.models import Coordinates
from onegov.gis.forms import CoordinatesField


def test_coordinates_field():
    field = CoordinatesField().bind(Form(), 'coordinates')

    template = (
        '<input class="coordinates" id="coordinates" name="coordinates" '
        'type="text" value="{}">'
    )

    assert not field.data

    assert field.data.lat is None
    assert field.data.lon is None
    assert field() == template.format(b64encode(
        json.dumps({
            'lat': None,
            'lon': None,
            'zoom': None
        }).encode('ascii')
    ).decode('ascii'))

    field.process_formdata([b64encode(
        json.dumps({
            'lat': 47.05183585,
            'lon': 8.30576869173879
        }).encode('ascii')
    ).decode('ascii')])

    assert field.data.lat == 47.05183585
    assert field.data.lon == 8.30576869173879

    assert field() == template.format(b64encode(
        json.dumps({
            'lat': 47.05183585,
            'lon': 8.30576869173879,
            'zoom': None
        }).encode('ascii')
    ).decode('ascii'))

    field.process_data({
        'lat': 47.05183585,
        'lon': 8.30576869173879
    })

    assert field.data.lat == 47.05183585
    assert field.data.lon == 8.30576869173879

    class Test(object):
        pass

    test = Test()
    field.populate_obj(test, 'coordinates')

    assert test.coordinates['lat'] == 47.05183585
    assert test.coordinates['lon'] == 8.30576869173879

    field.data = Coordinates()
    field.populate_obj(test, 'coordinates')
    assert test.coordinates is None
