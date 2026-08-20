from __future__ import annotations

from tests.onegov.election_day.common import login
from unittest.mock import patch
from webtest import TestApp as Client
from webtest import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_upload_ech_unauthenticated(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    client.get('/upload-ech', status=403)


def test_upload_ech_submit(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()
    login(client)

    xml = b'<?xml version="1.0" encoding="utf-8"?><delivery/>'

    # Successful upload
    with patch(
        'onegov.election_day.views.upload.ech0252.import_ech',
        return_value=([], set(), set())
    ) as import_:
        page = client.get('/upload-ech')
        page.form['xml'] = Upload('delivery.xml', xml, 'text/xml')
        result = page.form.submit()

        assert import_.called
        assert 'Ihre Resultate wurden erfolgreich hochgeladen' in result

    # Failed upload (import returns errors)
    with patch(
        'onegov.election_day.views.upload.ech0252.import_ech',
    ) as import_:
        from onegov.election_day.formats.imports.common import FileImportError
        import_.return_value = (
            [FileImportError('Invalid file')], set(), set()
        )

        page = client.get('/upload-ech')
        page.form['xml'] = Upload('delivery.xml', xml, 'text/xml')
        result = page.form.submit()

        assert import_.called
        assert 'Invalid file' in result
