import transaction

from onegov.winterthur.collections import AddressCollection
from onegov_testing import Client as BaseClient


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
