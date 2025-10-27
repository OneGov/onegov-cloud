from __future__ import annotations

from onegov.gis import Coordinates
from tests.shared.utils import decode_map_value, encode_map_value


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_map_default_view(client: Client) -> None:
    client.login_admin()

    settings = client.get('/map-settings')

    assert not decode_map_value(settings.form['default_map_view'].value)

    settings.form['default_map_view'] = encode_map_value({
        'lat': 47, 'lon': 8, 'zoom': 12
    })
    settings.form.submit()

    settings = client.get('/map-settings')
    coordinates = decode_map_value(settings.form['default_map_view'].value)
    assert coordinates.lat == 47
    assert coordinates.lon == 8
    assert coordinates.zoom == 12

    edit = client.get('/editor/edit/page/1')
    assert 'data-default-lat="47"' in edit
    assert 'data-default-lon="8"' in edit
    assert 'data-default-zoom="12"' in edit


def test_map_set_marker(client: Client) -> None:
    client.login_admin()

    edit = client.get('/editor/edit/page/1')
    assert decode_map_value(edit.form['coordinates'].value) == Coordinates()
    page = edit.form.submit().follow()

    assert 'marker-map' not in page

    edit = client.get('/editor/edit/page/1')
    edit.form['coordinates'] = encode_map_value({
        'lat': 47, 'lon': 8, 'zoom': 12
    })
    page = edit.form.submit().follow()

    assert 'marker-map' in page
    assert 'data-lat="47"' in page
    assert 'data-lon="8"' in page
    assert 'data-zoom="12"' in page
