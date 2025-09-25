import pytest
import transaction

from datetime import timedelta
from freezegun import freeze_time
from functools import partial
from io import BytesIO
from mock import patch
from onegov.pdf import Pdf
from onegov.winterthur.collections import AddressCollection
from sedate import utcnow
from tests.shared import Client as BaseClient
from unittest.mock import Mock
from webtest import Upload


class Client(BaseClient):
    skip_n_forms = 1


def test_view_addresses(winterthur_app, streets_csv, addresses_csv):
    client = Client(winterthur_app)

    page = client.get('/streets')
    assert "Keine Strassen gefunden" in page

    transaction.begin()

    addresses = AddressCollection(winterthur_app.session())
    addresses.import_from_csv(streets_csv, addresses_csv)

    transaction.commit()

    page = client.get('/streets')
    assert "Zürcherstrasse" in page
    page = page.click("Zürcherstrasse")

    assert "Zürcherstrasse 100" in page
    assert "Schlosstal" in page
    assert "Töss" in page


@pytest.mark.xfail(reason="the remote host providing the csv might be down")
def test_view_addresses_update_info(
    winterthur_app, streets_csv, addresses_csv
):
    client = Client(winterthur_app)
    transaction.begin()
    addresses = AddressCollection(winterthur_app.session())
    addresses.import_from_csv(streets_csv, addresses_csv)
    transaction.commit()

    page = client.get('/streets')
    assert "Zuletzt aktualisiert:" in page
    assert "failed" in page

    transaction.begin()
    AddressCollection(winterthur_app.session()).update()
    transaction.commit()

    page = client.get('/streets')
    assert "failed" not in page

    with freeze_time(utcnow() + timedelta(days=2)):
        page = client.get('/streets')
        assert "failed" in page


def test_view_shift_schedule(winterthur_app):

    def run(content, *args):
        filename = [
            arg.split('=')[-1] for arg in args[0] if 'sOutputFile' in arg
        ][0]
        with open(filename, 'wb') as file:
            file.write(content)
        return Mock()

    def pdf(content):
        result = BytesIO()
        pdf = Pdf(result)
        pdf.init_report()
        pdf.p(content)
        pdf.generate()
        result.seek(0)
        return result.read()

    client = Client(winterthur_app)
    client.login_admin()

    # No file yet
    assert not client.get('/shift-schedule').pyquery(
        'img.shift-schedule'
    )
    assert not winterthur_app.filestorage.listdir('')

    # Private file
    with freeze_time('2021-01-01'):
        page = client.get('/files')
        page.form['file'] = [Upload('test-1.pdf', pdf('Some content.'))]
        page = page.form.submit()
        url = page.pyquery('div[ic-get-from]')[0].attrib['ic-get-from']
        assert '01.01.2021 01:00' in client.get('/files')

    page = client.get(url)
    assert 'Öffentlich' in page
    assert 'Privat' not in page
    client.post(page.pyquery('a.is-published')[0].attrib['ic-post-to'])
    page = client.get(url)
    assert 'Öffentlich' not in page
    assert 'Privat' in page

    assert not client.get('/shift-schedule').pyquery(
        'img.shift-schedule'
    )
    assert not winterthur_app.filestorage.listdir('')

    # Published file
    client.post(page.pyquery('a.is-not-published')[0].attrib['ic-post-to'])
    page = client.get(url)
    assert 'Öffentlich' in page
    assert 'Privat' not in page

    with freeze_time('2020-01-01'):
        with patch('onegov.winterthur.app.subprocess') as subprocess:
            subprocess.run = partial(run, b'ABC')
            image = client.get('/shift-schedule').pyquery(
                'img.shift-schedule'
            )[0]
            assert 'QUJD' in image.attrib['src']
            assert winterthur_app.filestorage.listdir('') == [
                'shift-schedule-1609459200.0.png'
            ]

    # Upload a newer file
    with freeze_time('2022-01-01'):
        page = client.get('/files')
        page.form['file'] = [Upload('test-2.pdf', pdf('Some other content.'))]
        page.form.submit()
        assert '01.01.2022 01:00' in client.get('/files')

    with patch('onegov.winterthur.app.subprocess') as subprocess:
        subprocess.run = partial(run, b'XYZ')
        image = client.get('/shift-schedule').pyquery(
            'img.shift-schedule'
        )[0]
        assert 'WFla' in image.attrib['src']
        assert sorted(winterthur_app.filestorage.listdir('')) == [
            'shift-schedule-1609459200.0.png',
            'shift-schedule-1640995200.0.png'
        ]

    # Uplad a new file (but not a PDF)
    with freeze_time('2023-01-01'):
        page = client.get('/files')
        page.form['file'] = [Upload('test-1.text', b'Some Text.')]
        page = page.form.submit()
        assert '01.01.2023 01:00' in client.get('/files')

        image = client.get('/shift-schedule').pyquery(
            'img.shift-schedule'
        )[0]
        assert 'WFla' in image.attrib['src']
        assert sorted(winterthur_app.filestorage.listdir('')) == [
            'shift-schedule-1609459200.0.png',
            'shift-schedule-1640995200.0.png'
        ]
