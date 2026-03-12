from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from onegov.core.collection import GenericCollection
from onegov.core.csv import CSVFile
from onegov.core.orm import as_selectable
from onegov.winterthur.models import WinterthurAddress
from pycurl import Curl, URL, WRITEDATA
from sedate import utcnow
from sqlalchemy import select, func


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.core.csv import DefaultRow
    from sqlalchemy.engine import Result
    from sqlalchemy.orm import Query, Session
    from typing import NamedTuple

    class StreetRow(NamedTuple):
        letter: str
        street: str


HOST = 'https://stadt.winterthur.ch'
STREETS = f'{HOST}/_static/strassenverzeichnis/gswpl_strver_str.csv'
ADDRESSES = f'{HOST}/_static/strassenverzeichnis/gswpl_strver_adr.csv'


class AddressCollection(GenericCollection[WinterthurAddress]):

    @property
    def model_class(self) -> type[WinterthurAddress]:
        return WinterthurAddress

    def streets(self) -> Result[StreetRow]:
        query = as_selectable("""
            SELECT
                UPPER(UNACCENT(LEFT(street, 1))) AS letter, -- Text
                street                                      -- Text
            FROM
                winterthur_addresses
            GROUP BY
                street
            ORDER BY
                unaccent(street)
        """)

        return self.session.execute(select(*query.c))

    def last_updated(self) -> datetime | None:
        result = self.query().first()
        return result.modified if result else None

    def update_state(self) -> Literal['failed', 'ok']:
        last_updated = self.last_updated()
        if not last_updated:
            return 'failed'

        diff = utcnow() - last_updated
        diff_hours = (diff.days * 24) + (diff.seconds / 3600)
        if diff_hours > 24:
            return 'failed'

        return 'ok'

    def update(
        self,
        streets: str = STREETS,
        addresses: str = ADDRESSES
    ) -> None:
        self.delete_existing()
        self.import_from_csv(*self.load_urls(streets, addresses))

    def delete_existing(self) -> None:
        for address in self.query():
            self.session.delete(address)

    def import_from_csv(
        self,
        streets: CSVFile[DefaultRow],
        addresses: CSVFile[DefaultRow]
    ) -> None:

        streets_d = {s.strc: s.bez for s in streets.lines}

        addressless = set(streets_d.keys())
        max_id = 0

        for r in addresses.lines:
            addressless.discard(r.strc)

            address = WinterthurAddress()
            address.id = int(r.einid)
            address.street_id = int(r.strc)
            address.street = streets_d[r.strc]
            address.house_number = int(r.hnr)
            address.house_extra = r.hnrzu
            address.zipcode = int(r.plz)
            address.zipcode_extra = None if r.plzzu is None else int(r.plzzu)
            address.place = r.ort
            address.district = r.kreisname
            address.neighbourhood = r.quartiername

            self.session.add(address)

            max_id = max(max_id, address.id)

        # some streets do not have addresses -> we write a special record for
        # those streets so they still show up in our UI
        #
        # not the most elegant solution, but better than introducing a separate
        # table at least for now
        for id, key in enumerate(addressless, start=max_id + 1):
            address = self.model_class.as_addressless(int(key), streets_d[key])
            address.id = id

            self.session.add(address)

        self.session.flush()

    def load_urls(self, *urls: str) -> tuple[CSVFile[DefaultRow], ...]:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = (executor.submit(self.load_url, url) for url in urls)
            return tuple(f.result() for f in futures)

    def load_url(self, url: str) -> CSVFile[DefaultRow]:
        buffer = BytesIO()

        c = Curl()
        c.setopt(URL, url)
        c.setopt(WRITEDATA, buffer)
        c.perform()
        c.close()

        return CSVFile(buffer)


class AddressSubsetCollection(GenericCollection[WinterthurAddress]):

    def __init__(self, session: Session, street: str) -> None:
        super().__init__(session)
        self.street = street

    @property
    def model_class(self) -> type[WinterthurAddress]:
        return WinterthurAddress

    def subset(self) -> Query[WinterthurAddress]:
        subset = self.query().filter_by(street=self.street)

        return subset.order_by(
            func.unaccent(WinterthurAddress.street),
            WinterthurAddress.house_number,
            WinterthurAddress.house_extra
        )

    def exists(self) -> bool:
        return self.session.query(self.subset().exists()).scalar()
