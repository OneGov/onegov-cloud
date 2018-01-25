from onegov.winterthur.collections import AddressCollection


def test_synchronise_addresses(session):
    addresses = AddressCollection(session)
    addresses.synchronise()

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
    addresses.synchronise()
    assert count == addresses.query().count()

    # check the encoding
    a = addresses.query().filter_by(street="Alte Römerstrasse").first()
    assert a.street == "Alte Römerstrasse"
