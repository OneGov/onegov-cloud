from csv import writer
from datetime import datetime
from onegov.wtfs.models.municipality import Municipality
from onegov.wtfs.models.scan_job import ScanJob


class Invoice(object):

    def __init__(self, session):
        self.session = session
        self.from_date = None
        self.to_date = None
        self.cs2_user = None
        self.subject = None
        self.municipality_id = None
        self.accounting_unit = None
        self.revenue_account = None

    def export(self, file):
        csv = writer(file, delimiter=';')
        now = datetime.now()
        current_date = f'{now:%Y-%m-%d}'
        current_time = f'{now:%H.%M.%S}'

        query = self.session.query(ScanJob)
        query = query.join(Municipality)
        if self.from_date:
            query = query.filter(ScanJob.dispatch_date >= self.from_date)
        if self.to_date:
            query = query.filter(ScanJob.dispatch_date <= self.to_date)
        if self.municipality_id:
            query = query.filter(
                ScanJob.municipality_id == self.municipality_id
            )
        query = query.order_by(
            Municipality.meta['gpn_number'],
            ScanJob.delivery_number
        )

        item_number = 1
        municipality_count = 0
        last_municipality = None
        for scan_job in query:
            municipality = scan_job.municipality
            if municipality == last_municipality:
                item_number += 1
            else:
                item_number = 1
                municipality_count += 1

            csv.writerow((
                f'{now:%Y%m%d}{municipality_count}',
                current_date,
                current_time,
                f'{municipality.gpn_number:08}',
                f'{item_number:05}',
                f'{municipality.gpn_number:08}',
                self.subject,
                f'{item_number:05}',
                f'{item_number:03}',
                current_date,
                current_date,
                current_date,
                f'{municipality.gpn_number:08}',
                f'{int((scan_job.return_scanned_tax_forms or 0) * 1000):+018}',
                f'Lieferscheinnummer {scan_job.delivery_number}',
                f'{int(municipality.price_per_quantity * 10000000):+018}',
                f'{int(municipality.price_per_quantity * 10000000):+018}',
                '1',
                current_date,
                municipality.address_supplement or '',
                self.cs2_user,
                '000',
                self.accounting_unit,
                self.revenue_account,
            ))

            last_municipality = municipality
