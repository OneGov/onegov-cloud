import transaction

from datetime import timedelta
from freezegun import freeze_time
from io import BytesIO
from mock import patch
from onegov.winterthur.collections import AddressCollection
from sedate import utcnow
from tests.shared import Client as BaseClient
from webtest import Upload


class Client(BaseClient):
    skip_first_form = True


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
    client = Client(winterthur_app)
    client.login_admin()

    page = client.get('/files/shift-schedule')
    assert 'img' not in page

    with patch('onegov.winterthur.app.WinterthurApp.get_shift_schedule_image',
               return_value=BytesIO()):

        page = client.get('/files')
        page.form['file'] = Upload('Test2.pdf', b'File content.')
        page.form.submit()

        page = client.get('/files/shift-schedule')
        assert 'img' in page
