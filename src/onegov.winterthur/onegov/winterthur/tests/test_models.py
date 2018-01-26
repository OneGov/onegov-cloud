import pytest

from onegov.winterthur.collections import AddressCollection


@pytest.mark.xfail(reason="the remote host providing the csv might be down")
def test_download_addresses(session):
    addresses = AddressCollection(session)
    addresses.update()

    assert addresses.query().count() >= 18_000


def test_update_adresses(session, streets_csv, addresses_csv):
    addresses = AddressCollection(session)
    addresses.update_by_csv(streets_csv, addresses_csv)

    count = addresses.query().count()

    # check a rough address count
    assert count >= 18_000

    # check a well known record
    a = addresses.query().first()
    assert a.id == 9236
    assert a.street == 'Ackeretstrasse'
    assert a.house_number == 1
    assert a.house_extra == ''
    assert a.zipcode == 8400
    assert a.zipcode_extra == 0
    assert a.place == 'Winterthur'
    assert a.district == 'Winterthur-Stadt'

    # synchronise again -> the count should stay the same
    addresses.update()
    assert count == addresses.query().count()

    # check the encoding
    a = addresses.query().filter_by(street="Alte Römerstrasse").first()
    assert a.street == "Alte Römerstrasse"
