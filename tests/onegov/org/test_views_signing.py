from __future__ import annotations

import re
import transaction
import vcr  # type: ignore[import-untyped]

from onegov.core.utils import module_path
from onegov.file import FileCollection
from onegov.user import UserCollection
from unittest.mock import patch
from webtest import Upload
from yubico_client import Yubico  # type: ignore[import-untyped]


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.client import ExtendedResponse
    from .conftest import Client


def test_sign_document(client: Client) -> None:
    client.login_admin()

    path = module_path('tests.onegov.org', 'fixtures/sample.pdf')
    with open(path, 'rb') as f:
        page = client.get('/files')
        page.form['file'] = [Upload('Sample.pdf', f.read(), 'application/pdf')]
        page.form.submit()

    pdf = FileCollection(client.app.session()).query().one()

    # seals are only used if yubikeys are used
    page = client.get(f'/storage/{pdf.id}/details')
    assert 'Siegel' not in page

    client.app.enable_yubikey = True

    page = client.get(f'/storage/{pdf.id}/details')
    assert 'Siegel' in page

    # applying a seal only works if the given user has a yubikey setup
    def sign(
        client: Client,
        page: ExtendedResponse,
        token: str
    ) -> ExtendedResponse:
        rex = r'"(http://\w+/\w+/\w+/sign?[^"]+)"'
        url = re.search(rex, page.text).group(1)  # type: ignore[union-attr]
        return client.post(url, {'token': token})

    assert "Bitte geben Sie Ihren Yubikey ein" in sign(client, page, '')
    assert "nicht mit einem Yubikey verknüpft" in sign(client, page, 'foobar')

    # not just any yubikey either, it has to be the one linked to the account
    transaction.begin()

    user = (UserCollection(client.app.session())
        .by_username('admin@example.org'))

    assert user is not None
    user.second_factor = {
        'type': 'yubikey',
        'data': 'ccccccbcgujh'
    }

    transaction.commit()

    assert "nicht mit Ihrem Konto verknüpft" in sign(client, page, 'foobar')

    # if the key doesn't work, the seal is not applied
    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = False

        assert "konnte nicht validiert werden" in sign(
            client, page, 'ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded')

    assert not FileCollection(client.app.session()).query().one().signed

    # once the seal has been applied, it can't be repeated
    tape = module_path('tests.onegov.org', 'cassettes/ais-success.json')

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = True

        with vcr.use_cassette(tape, record_mode='none'):

            assert "Digitales Siegel angewendet von admin@example.org" in sign(
                client, page, 'ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded')

        with vcr.use_cassette(tape, record_mode='none'):

            assert "Diese Datei hat bereits ein digitales Siegel" in sign(
                client, page, 'ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded')

    # we should at this point see some useful metadata on the file
    metadata = (FileCollection(client.app.session())
        .query().one().signature_metadata)

    assert metadata is not None
    assert metadata['token'] == 'ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    assert metadata['signee'] == 'admin@example.org'

    # and we should see a message in the activity log
    assert 'Datei signiert' in client.get('/timeline')

    # deleting the file with applied seal
    # at this point should yield another message
    pdf = FileCollection(client.app.session()).query().one()
    client.get(f'/storage/{pdf.id}/details').click("Löschen")
    assert 'Datei mit digitalem Siegel gelöscht' in client.get(
        '/timeline').text
