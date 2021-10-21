from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from onegov.core.collection import GenericCollection
from onegov.core.csv import CSVFile
from onegov.core.orm import as_selectable
from onegov.winterthur.models import WinterthurAddress
from pycurl import Curl
from sqlalchemy import select, func

HOST = 'https://stadt.winterthur.ch'
STREETS = f'{HOST}/_static/strassenverzeichnis/gswpl_strver_str.csv'
ADDRESSES = f'{HOST}/_static/strassenverzeichnis/gswpl_strver_adr.csv'


class AddressCollection(GenericCollection):

    @property
    def model_class(self):
        return WinterthurAddress

    def streets(self):
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

        return self.session.execute(select(query.c))

    def update(self, streets=STREETS, addresses=ADDRESSES):
        self.delete_existing()
        self.import_from_csv(*self.load_urls(streets, addresses))

    def delete_existing(self):
        for address in self.query():
            self.session.delete(address)

    def import_from_csv(self, streets, addresses):
        streets = {s.strc: s.bez for s in streets.lines}

        addressless = set(streets.keys())
        max_id = 0

        for r in addresses.lines:
            addressless.discard(r.strc)

            address = WinterthurAddress()
            address.id = int(r.einid)
            address.street_id = int(r.strc)
            address.street = streets[r.strc]
            address.house_number = int(r.hnr)
            address.house_extra = r.hnrzu
            address.zipcode = int(r.plz)
            address.zipcode_extra = r.plzzu
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
            address = self.model_class.as_addressless(int(key), streets[key])
            address.id = id

            self.session.add(address)

        self.session.flush()

    def load_urls(self, *urls):
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = (executor.submit(self.load_url, url) for url in urls)
            return tuple(f.result() for f in futures)

    def load_url(self, url):
        buffer = BytesIO()

        c = Curl()
        c.setopt(c.URL, url)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()

        return CSVFile(buffer)


class AddressSubsetCollection(GenericCollection):

    def __init__(self, session, street):
        super().__init__(session)
        self.street = street

    @property
    def model_class(self):
        return WinterthurAddress

    def subset(self):
        subset = self.query().filter_by(street=self.street)

        return subset.order_by(
            func.unaccent(WinterthurAddress.street),
            WinterthurAddress.house_number,
            WinterthurAddress.house_extra
        )

    def exists(self):
        return self.session.query(self.subset().exists()).scalar()
