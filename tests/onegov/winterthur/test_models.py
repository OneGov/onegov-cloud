from __future__ import annotations

import math
import pytest

from onegov.winterthur.collections import AddressCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.csv import CSVFile
    from sqlalchemy.orm import Session


@pytest.mark.xfail(reason="the remote host providing the csv might be down")
def test_download_addresses(session: Session) -> None:
    addresses = AddressCollection(session)
    addresses.update()

    assert addresses.query().count() >= 18_000


@pytest.mark.xfail(reason="the remote host providing the csv might be down")
def test_update_addresses(
    session: Session,
    streets_csv: CSVFile,
    addresses_csv: CSVFile
) -> None:
    addresses = AddressCollection(session)
    addresses.import_from_csv(streets_csv, addresses_csv)

    count = addresses.query().count()

    # check a rough address count
    assert count >= 18_000

    # check a well known record
    a = addresses.query().first()
    assert a is not None
    assert a.id == 9236
    assert a.street == 'Ackeretstrasse'
    assert a.house_number == 1
    assert a.house_extra == ''
    assert a.zipcode == 8400
    assert a.zipcode_extra == 0
    assert a.place == 'Winterthur'
    assert a.district == 'Winterthur-Stadt'

    # synchronise again -> the count should roughly stay the same
    # if not, the file on the remote end has been updated!
    addresses.update()
    assert math.isclose(count, addresses.query().count(), rel_tol=0.1)

    # check the encoding
    a = addresses.query().filter_by(street="Alte Römerstrasse").first()
    assert a is not None
    assert a.street == "Alte Römerstrasse"
