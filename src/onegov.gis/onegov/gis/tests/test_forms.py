from onegov.form import Form
from onegov.gis.forms import MapPointField


def test_mappoint_field():
    field = MapPointField().bind(Form(), 'point')

    template = (
        '<input class="map-point" id="point" name="point" '
        'type="text" value="{}">'
    )

    assert not field.data

    assert field.data.lat is None
    assert field.data.lon is None
    assert field() == template.format('')

    field.process_formdata(['47.05183585/8.30576869173879'])

    assert field.data.lat == 47.05183585
    assert field.data.lon == 8.30576869173879

    field.data.lat = '47.05183585'
    assert field.data.lat == 47.05183585

    field.data.lon = '8.30576869173879'
    assert field.data.lon == 8.30576869173879

    assert field() == template.format('47.05183585/8.30576869173879')
