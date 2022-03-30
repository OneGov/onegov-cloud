import transaction

from sedate import utcnow
from freezegun import freeze_time
from datetime import timedelta
from onegov.winterthur.collections import AddressCollection
from tests.shared import Client as BaseClient


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
