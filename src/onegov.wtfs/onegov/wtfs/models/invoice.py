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
        csv = writer(file)
        now = datetime.now()
        current_date_1 = f'{now:%Y%m%d}1'
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

        count = 1
        last_gpn_number = None
        for scan_job in query:
            municipality = scan_job.municipality
            gpn_number = municipality.gpn_number
            gpn_number = str(gpn_number) if gpn_number is not None else ''
            count = count + 1 if gpn_number == last_gpn_number else 1
            last_gpn_number = gpn_number
            address_supplement = municipality.address_supplement or ''
            price_per_quantity = municipality.price_per_quantity
            price_per_quantity = str(int(price_per_quantity * 10000000))
            # todo: this seems to be wrong
            tax_forms = (
                (scan_job.dispatch_tax_forms or 0)
                - (scan_job.return_unscanned_tax_forms or 0)
            )
            csv.writerow((
                current_date_1,
                current_date,
                current_time,
                gpn_number,
                str(count),
                gpn_number,
                self.subject,
                str(count),
                current_date,
                current_date,
                current_date,
                gpn_number,
                str(tax_forms * 1000),
                f'Lieferscheinnummer {scan_job.delivery_number}',
                price_per_quantity,
                price_per_quantity,
                '1',
                current_date,
                address_supplement,
                self.cs2_user,
                self.accounting_unit,
                self.revenue_account,
            ))
