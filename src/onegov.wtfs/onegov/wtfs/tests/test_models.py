from datetime import date
from freezegun import freeze_time
from io import StringIO
from onegov.user import User
from onegov.wtfs.models import DailyListBoxes
from onegov.wtfs.models import DailyListBoxesAndForms
from onegov.wtfs.models import Invoice
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Notification
from onegov.wtfs.models import PaymentType
from onegov.wtfs.models import PickupDate
from onegov.wtfs.models import Principal
from onegov.wtfs.models import ReportBoxes
from onegov.wtfs.models import ReportBoxesAndForms
from onegov.wtfs.models import ReportBoxesAndFormsByDelivery
from onegov.wtfs.models import ReportFormsByMunicipality
from onegov.wtfs.models import ScanJob
from onegov.wtfs.models import UserManual
from uuid import uuid4


def test_principal():
    principal = Principal()
    assert principal


def test_payment_type(session):
    session.add(PaymentType(name='normal', _price_per_quantity=700))
    session.flush()

    payment_type = session.query(PaymentType).one()
    assert payment_type.name == 'normal'
    assert payment_type._price_per_quantity == 700
    assert payment_type.price_per_quantity == 7.0

    payment_type.price_per_quantity = 8.5
    assert payment_type._price_per_quantity == 850
    assert payment_type.price_per_quantity == 8.5


def test_municipality(session):
    session.add(PaymentType(name='normal', _price_per_quantity=700))
    session.add(PaymentType(name='spezial', _price_per_quantity=850))

    session.add(
        Municipality(
            name='Winterthur',
            bfs_number=230,
            address_supplement='Zusatz',
            gpn_number=1120,
            payment_type='normal'
        )
    )
    session.flush()

    municipality = session.query(Municipality).one()
    assert municipality.name == 'Winterthur'
    assert municipality.bfs_number == 230
    assert municipality.address_supplement == 'Zusatz'
    assert municipality.gpn_number == 1120
    assert municipality.price_per_quantity == 7.0
    assert not municipality.has_data

    municipality.payment_type = 'spezial'
    assert municipality.price_per_quantity == 8.5

    municipality.payment_type = 'invalid'
    assert municipality.price_per_quantity == 0

    # PickupDate
    session.add(
        PickupDate(municipality_id=municipality.id, date=date(2019, 1, 1))
    )
    session.add(
        PickupDate(municipality_id=municipality.id, date=date(2019, 1, 7))
    )
    session.add(
        PickupDate(municipality_id=municipality.id, date=date(2019, 1, 14))
    )
    session.flush()
    session.expire_all()

    assert [d.date for d in municipality.pickup_dates] == [
        date(2019, 1, 1), date(2019, 1, 7), date(2019, 1, 14)
    ]
    assert session.query(PickupDate).first().municipality == municipality
    assert municipality.has_data

    # Contacts
    assert municipality.contacts == []
    for name, group_id, data in (
        ('a', municipality.id, None),
        ('b', municipality.id, {}),
        ('c', municipality.id, {'contact': None}),
        ('d', municipality.id, {'contact': False}),
        ('e', municipality.id, {'contact': True}),
        ('f', municipality.id, {'contact': True}),
        ('g', None, {'contact': True}),
    ):
        session.add(
            User(
                realname=name,
                username=f'{name}@example.org',
                password_hash='abcd',
                role='editor',
                group_id=group_id,
                data=data
            )
        )
    assert municipality.contacts == ['e@example.org', 'f@example.org']


def test_scan_job(session):
    session.add(Municipality(name='Winterthur', bfs_number=230))
    session.flush()
    municipality = session.query(Municipality).one()

    session.add(
        ScanJob(
            type='normal',
            municipality_id=municipality.id,
            delivery_number=1,
            dispatch_date=date(2019, 1, 1),
            dispatch_note='Dispatch note',
            dispatch_boxes=1,
            dispatch_tax_forms_current_year=2,
            dispatch_tax_forms_last_year=3,
            dispatch_tax_forms_older=4,
            dispatch_single_documents=5,
            dispatch_cantonal_tax_office=6,
            dispatch_cantonal_scan_center=7,
            return_date=date(2019, 2, 2),
            return_note='Return note',
            return_boxes=8,
            return_tax_forms_current_year=9,
            return_tax_forms_last_year=10,
            return_tax_forms_older=11,
            return_single_documents=12,
            return_unscanned_tax_forms_current_year=16,
            return_unscanned_tax_forms_last_year=15,
            return_unscanned_tax_forms_older=14,
            return_unscanned_single_documents=13,
        )
    )
    session.flush()

    scan_job = session.query(ScanJob).one()
    assert scan_job.municipality == municipality
    assert scan_job.delivery_number == 1
    assert scan_job.title.interpolate() == 'Scan job no. 1'
    assert scan_job.type == 'normal'
    assert scan_job.municipality_id == municipality.id
    assert scan_job.dispatch_date == date(2019, 1, 1)
    assert scan_job.dispatch_note == 'Dispatch note'
    assert scan_job.dispatch_boxes == 1
    assert scan_job.dispatch_tax_forms_current_year == 2
    assert scan_job.dispatch_tax_forms_last_year == 3
    assert scan_job.dispatch_tax_forms_older == 4
    assert scan_job.dispatch_tax_forms == 2 + 3 + 4
    assert scan_job.dispatch_single_documents == 5
    assert scan_job.dispatch_cantonal_tax_office == 6
    assert scan_job.dispatch_cantonal_scan_center == 7
    assert scan_job.return_date == date(2019, 2, 2)
    assert scan_job.return_note == 'Return note'
    assert scan_job.return_boxes == 8
    assert scan_job.return_tax_forms_current_year == 9
    assert scan_job.return_tax_forms_last_year == 10
    assert scan_job.return_tax_forms_older == 11
    assert scan_job.return_tax_forms == 9 + 10 + 11
    assert scan_job.return_single_documents == 12
    assert scan_job.return_unscanned_tax_forms_current_year == 16
    assert scan_job.return_unscanned_tax_forms_last_year == 15
    assert scan_job.return_unscanned_tax_forms_older == 14
    assert scan_job.return_unscanned_tax_forms == 16 + 15 + 14
    assert scan_job.return_unscanned_single_documents == 13
    assert scan_job.return_scanned_tax_forms_current_year == 9 - 16
    assert scan_job.return_scanned_tax_forms_last_year == 10 - 15
    assert scan_job.return_scanned_tax_forms_older == 11 - 14
    assert scan_job.return_scanned_tax_forms == 9 + 10 + 11 - 16 - 15 - 14
    assert scan_job.return_scanned_single_documents == 12 - 13

    assert session.query(
        ScanJob.dispatch_boxes,
        ScanJob.dispatch_tax_forms_current_year,
        ScanJob.dispatch_tax_forms_last_year,
        ScanJob.dispatch_tax_forms_older,
        ScanJob.dispatch_tax_forms,
        ScanJob.dispatch_single_documents,
        ScanJob.dispatch_cantonal_tax_office,
        ScanJob.dispatch_cantonal_scan_center,
        ScanJob.return_boxes,
        ScanJob.return_tax_forms_current_year,
        ScanJob.return_tax_forms_last_year,
        ScanJob.return_tax_forms_older,
        ScanJob.return_tax_forms,
        ScanJob.return_single_documents,
        ScanJob.return_unscanned_tax_forms_current_year,
        ScanJob.return_unscanned_tax_forms_last_year,
        ScanJob.return_unscanned_tax_forms_older,
        ScanJob.return_unscanned_tax_forms,
        ScanJob.return_unscanned_single_documents,
        ScanJob.return_scanned_tax_forms_current_year,
        ScanJob.return_scanned_tax_forms_last_year,
        ScanJob.return_scanned_tax_forms_older,
        ScanJob.return_scanned_tax_forms,
        ScanJob.return_scanned_single_documents,
    ).one() == (
        1,
        2,
        3,
        4,
        2 + 3 + 4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        9 + 10 + 11,
        12,
        16,
        15,
        14,
        16 + 15 + 14,
        13,
        9 - 16,
        10 - 15,
        11 - 14,
        9 + 10 + 11 - 16 - 15 - 14,
        12 - 13,
    )

    assert municipality.scan_jobs.one() == scan_job
    assert municipality.has_data


def add_report_data(session):
    data = {
        'Adlikon': {
            'municipality_id': uuid4(),
            'bfs_number': 21,
            'jobs': [
                [date(2019, 1, 1), 1, 2, 3, date(2019, 1, 2), 4],
                [date(2019, 1, 2), 3, 2, 1, date(2019, 1, 3), 1],
            ]
        },
        'Aesch': {
            'municipality_id': uuid4(),
            'bfs_number': 241,
            'jobs': [
                [date(2019, 1, 1), 1, 2, 3, date(2019, 1, 2), 4],
                [date(2019, 1, 3), 0, 10, None, date(2019, 1, 4), None],
            ]
        },
        'Altikon': {
            'municipality_id': uuid4(),
            'bfs_number': 211,
            'jobs': [
                [date(2019, 1, 2), 1, 2, 3, date(2019, 1, 2), 4],
            ]
        },
        'Andelfingen': {
            'municipality_id': uuid4(),
            'bfs_number': 30,
            'jobs': [
                [date(2019, 1, 2), 1, 2, 3, date(2019, 1, 4), 4],
            ]
        },
    }

    delivery_number = 1
    for name, values in data.items():
        session.add(Municipality(
            name=name,
            id=values['municipality_id'],
            bfs_number=values['bfs_number']
        ))
        for job in values['jobs']:
            double = [2 * v if isinstance(v, int) else v for v in job]
            session.add(
                ScanJob(
                    type='normal',
                    municipality_id=values['municipality_id'],
                    delivery_number=delivery_number,
                    dispatch_date=job[0],
                    dispatch_boxes=job[1],
                    dispatch_cantonal_tax_office=job[2],
                    dispatch_cantonal_scan_center=job[3],
                    dispatch_tax_forms_older=job[1],
                    dispatch_tax_forms_last_year=job[2],
                    dispatch_tax_forms_current_year=job[3],
                    dispatch_single_documents=job[5],
                    return_tax_forms_older=double[1],
                    return_tax_forms_last_year=double[2],
                    return_tax_forms_current_year=double[3],
                    return_single_documents=double[5],
                    return_unscanned_tax_forms_older=job[1],
                    return_unscanned_tax_forms_last_year=job[2],
                    return_unscanned_tax_forms_current_year=job[3],
                    return_unscanned_single_documents=job[5],
                    return_date=job[4],
                    return_boxes=job[5],
                )
            )
            delivery_number += 1
        session.flush()
    session.flush()


def test_daily_list_boxes(session):
    daily_list = DailyListBoxes(session, date_=date.today())
    assert daily_list.query().all() == []
    assert daily_list.total() == (0, 0, 0, 0)

    add_report_data(session)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 1))
    assert daily_list.query().all() == [
        ('Adlikon', 21, 1, 2, 3, 0),
        ('Aesch', 241, 1, 2, 3, 0)
    ]
    assert daily_list.total() == (2, 4, 6, 0)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 2))
    assert daily_list.query().all() == [
        ('Adlikon', 21, 3, 2, 1, 4),
        ('Aesch', 241, 0, 0, 0, 4),
        ('Altikon', 211, 1, 2, 3, 4),
        ('Andelfingen', 30, 1, 2, 3, 0)
    ]
    assert daily_list.total() == (5, 6, 7, 12)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 3))
    assert daily_list.query().all() == [
        ('Adlikon', 21, 0, 0, 0, 1),
        ('Aesch', 241, 0, 10, 0, 0)
    ]
    assert daily_list.total() == (0, 10, 0, 1)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 4))
    assert daily_list.query().all() == [
        ('Aesch', 241, 0, 0, 0, 0),
        ('Andelfingen', 30, 0, 0, 0, 4)
    ]
    assert daily_list.total() == (0, 0, 0, 4)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 5))
    assert daily_list.query().all() == []
    assert daily_list.total() == (0, 0, 0, 0)


def test_daily_list_boxes_and_forms(session):
    daily_list = DailyListBoxesAndForms(session, date_=date.today())
    assert daily_list.query().all() == []
    assert daily_list.total() == (0, 0, 0, 0, 0, 0, 0)

    add_report_data(session)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 1))
    assert daily_list.query().all() == [
        ('Adlikon', 21, 1, 1, 2, 3, 4, 2, 3),
        ('Aesch', 241, 1, 1, 2, 3, 4, 2, 3)
    ]
    assert daily_list.total() == (2, 2, 4, 6, 8, 4, 6)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 2))

    assert daily_list.query().all() == [
        ('Adlikon', 21, 3, 3, 2, 1, 1, 2, 1),
        ('Aesch', 241, 0, 0, 0, 0, 0, 0, 0),
        ('Altikon', 211, 1, 1, 2, 3, 4, 2, 3),
        ('Andelfingen', 30, 1, 1, 2, 3, 4, 2, 3)
    ]
    assert daily_list.total() == (5, 5, 6, 7, 9, 6, 7)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 3))
    assert daily_list.query().all() == [
        ('Adlikon', 21, 0, 0, 0, 0, 0, 0, 0),
        ('Aesch', 241, 0, 0, 10, 0, 0, 10, 0)
    ]
    assert daily_list.total() == (0, 0, 10, 0, 0, 10, 0)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 4))
    assert daily_list.query().all() == [
        ('Aesch', 241, 0, 0, 0, 0, 0, 0, 0),
        ('Andelfingen', 30, 0, 0, 0, 0, 0, 0, 0)
    ]
    assert daily_list.total() == (0, 0, 0, 0, 0, 0, 0)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 5))
    assert daily_list.query().all() == []
    assert daily_list.total() == (0, 0, 0, 0, 0, 0, 0)


def test_report_boxes(session):
    def _report(start, end):
        return ReportBoxes(session, start=start, end=end)

    report = _report(date.today(), date.today())
    assert report.query().all() == []
    assert report.total() == (0, 0, 0, 0)

    add_report_data(session)

    report = _report(date(2019, 1, 1), date(2019, 1, 1))
    assert report.query().all() == [
        ('Adlikon', 21, 1, 2, 3, 4),
        ('Aesch', 241, 1, 2, 3, 4)
    ]
    assert report.total() == (2, 4, 6, 8)

    report = _report(date(2019, 1, 2), date(2019, 1, 3))
    assert report.query().all() == [
        ('Adlikon', 21, 3, 2, 1, 1),
        ('Aesch', 241, 0, 10, 0, 0),
        ('Altikon', 211, 1, 2, 3, 4),
        ('Andelfingen', 30, 1, 2, 3, 4)
    ]
    assert report.total() == (5, 16, 7, 9)

    report = _report(date(2019, 1, 4), date(2019, 1, 5))
    assert report.query().all() == [
        ('Aesch', 241, 0, 0, 0, 0),
        ('Andelfingen', 30, 0, 0, 0, 0)
    ]
    assert report.total() == (0, 0, 0, 0)


def test_report_boxes_and_forms(session):
    def _report(start, end):
        return ReportBoxesAndForms(session, start=start, end=end)

    report = _report(date.today(), date.today())
    assert report.query().all() == []
    assert report.total() == (0, 0, 0, 0, 0, 0)

    add_report_data(session)

    report = _report(date(2019, 1, 1), date(2019, 1, 1))
    assert report.query().all() == [
        ('Adlikon', 21, 1, 2, 3, 6, 4, 4),
        ('Aesch', 241, 1, 2, 3, 6, 4, 4)
    ]
    assert report.total() == (2, 4, 6, 12, 8, 8)

    report = _report(date(2019, 1, 2), date(2019, 1, 3))
    assert report.query().all() == [
        ('Adlikon', 21, 3, 2, 1, 6, 1, 1),
        ('Aesch', 241, 0, 10, 0, 10, 0, 0),
        ('Altikon', 211, 1, 2, 3, 6, 4, 4),
        ('Andelfingen', 30, 1, 2, 3, 6, 4, 4)
    ]
    assert report.total() == (5, 16, 7, 28, 9, 9)

    report = _report(date(2019, 1, 4), date(2019, 1, 5))
    assert report.query().all() == [
        ('Aesch', 241, 0, 0, 0, 0, 0, 0),
        ('Andelfingen', 30, 0, 0, 0, 0, 0, 0)
    ]
    assert report.total() == (0, 0, 0, 0, 0, 0)


def test_report_forms_by_municipality(session):
    def _report(start, end, municipality):
        query = session.query(Municipality).filter_by(name=municipality)
        return ReportFormsByMunicipality(
            session, start=start, end=end, municipality_id=query.one().id
        )

    add_report_data(session)

    report = _report(date(2019, 1, 1), date(2019, 1, 1), 'Adlikon')
    assert report.query().all() == [('Adlikon', 21, 1, 2, 3, 6)]
    report = _report(date(2019, 1, 1), date(2019, 1, 1), 'Aesch')
    assert report.query().all() == [('Aesch', 241, 1, 2, 3, 6)]

    report = _report(date(2019, 1, 2), date(2019, 1, 3), 'Adlikon')
    assert report.query().all() == [('Adlikon', 21, 3, 2, 1, 6)]
    report = _report(date(2019, 1, 2), date(2019, 1, 3), 'Aesch')
    assert report.query().all() == [('Aesch', 241, 0, 10, 0, 10)]
    report = _report(date(2019, 1, 2), date(2019, 1, 3), 'Altikon')
    assert report.query().all() == [('Altikon', 211, 1, 2, 3, 6)]
    report = _report(date(2019, 1, 2), date(2019, 1, 3), 'Andelfingen')
    assert report.query().all() == [('Andelfingen', 30, 1, 2, 3, 6)]

    report = _report(date(2019, 1, 4), date(2019, 1, 5), 'Aesch')
    assert report.query().all() == [('Aesch', 241, 0, 0, 0, 0)]
    report = _report(date(2019, 1, 4), date(2019, 1, 5), 'Andelfingen')
    assert report.query().all() == [('Andelfingen', 30, 0, 0, 0, 0)]


def test_report_delivery(session):
    def _report(start, end, municipality):
        query = session.query(Municipality).filter_by(name=municipality)
        return ReportBoxesAndFormsByDelivery(
            session, start=start, end=end, type=None,
            municipality_id=query.one().id
        )

    add_report_data(session)

    # 2019-01-01
    report = _report(date(2019, 1, 1), date(2019, 1, 1), 'Adlikon')
    assert report.query().all() == [(date(2019, 1, 1), 1, 1, 2, 3, 6, 4, 4)]
    assert report.total() == (0, 0, 1, 2, 3, 6, 4, 4)

    report = _report(date(2019, 1, 1), date(2019, 1, 1), 'Aesch')
    assert report.query().all() == [(date(2019, 1, 1), 3, 1, 2, 3, 6, 4, 4)]
    assert report.total() == (0, 0, 1, 2, 3, 6, 4, 4)

    report = _report(date(2019, 1, 1), date(2019, 1, 1), 'Altikon')
    assert report.query().all() == []
    assert report.total() == (0, 0, 0, 0, 0, 0, 0, 0)

    report = _report(date(2019, 1, 1), date(2019, 1, 1), 'Andelfingen')
    assert report.query().all() == []
    assert report.total() == (0, 0, 0, 0, 0, 0, 0, 0)

    # 2019-01-01 ... 2019-01-05
    report = _report(date(2019, 1, 1), date(2019, 1, 5), 'Adlikon')
    assert report.query().all() == [
        (date(2019, 1, 1), 1, 1, 2, 3, 6, 4, 4),
        (date(2019, 1, 2), 2, 3, 2, 1, 6, 1, 1)
    ]
    assert report.total() == (0, 0, 4, 4, 4, 12, 5, 5)

    report = _report(date(2019, 1, 1), date(2019, 1, 5), 'Aesch')
    assert report.query().all() == [
        (date(2019, 1, 1), 3, 1, 2, 3, 6, 4, 4),
        (date(2019, 1, 3), 4, 0, 10, 0, 10, 0, None)
    ]
    assert report.total() == (0, 0, 1, 12, 3, 16, 4, 4)

    report = _report(date(2019, 1, 1), date(2019, 1, 5), 'Altikon')
    assert report.query().all() == [
        (date(2019, 1, 2), 5, 1, 2, 3, 6, 4, 4)
    ]
    assert report.total() == (0, 0, 1, 2, 3, 6, 4, 4)

    report = _report(date(2019, 1, 1), date(2019, 1, 5), 'Andelfingen')
    assert report.query().all() == [
        (date(2019, 1, 2), 6, 1, 2, 3, 6, 4, 4)
    ]
    assert report.total() == (0, 0, 1, 2, 3, 6, 4, 4)


def test_notification(session):

    class Identity():
        application_id = 'wtfs'
        userid = 'admin'

    class Request():
        def __init__(self, session):
            self.identity = Identity()
            self.session = session

    notification = Notification.create(
        Request(session),
        title="Lorem ipsum",
        text="Lorem ipsum dolor sit amet."
    )

    notification = session.query(Notification).one()
    assert notification.title == "Lorem ipsum"
    assert notification.text == "Lorem ipsum dolor sit amet."
    assert notification.channel_id == "wtfs"
    assert notification.owner == "admin"
    assert notification.type == "wtfs_notification"


def test_invoice(session):
    session.add(PaymentType(name='normal', _price_per_quantity=700))
    session.add(PaymentType(name='spezial', _price_per_quantity=850))

    session.add(
        Municipality(
            name='Adlikon',
            address_supplement='Finkenweg',
            gpn_number=8882255,
            bfs_number=21,
            payment_type='normal'
        )
    )
    session.add(
        Municipality(
            name='Aesch',
            address_supplement='Meisenweg',
            gpn_number=9993344,
            bfs_number=241,
            payment_type='spezial'
        )
    )
    session.flush()
    adlikon = session.query(Municipality).filter_by(name='Adlikon').one()
    aesch = session.query(Municipality).filter_by(name='Aesch').one()

    session.add(
        ScanJob(
            type='normal',
            municipality_id=adlikon.id,
            delivery_number=1,
            dispatch_date=date(2018, 12, 10),
            dispatch_boxes=1,
            dispatch_tax_forms_current_year=10,
            dispatch_tax_forms_last_year=20,
            dispatch_tax_forms_older=30,
            dispatch_single_documents=40,
            dispatch_cantonal_tax_office=5,
            dispatch_cantonal_scan_center=4,
            return_date=date(2018, 12, 20),
            return_boxes=1,
            return_tax_forms_current_year=9,
            return_tax_forms_last_year=18,
            return_tax_forms_older=27,
            return_single_documents=36,
            return_unscanned_tax_forms_current_year=1,
            return_unscanned_tax_forms_last_year=2,
            return_unscanned_tax_forms_older=3,
            return_unscanned_single_documents=4,
        )
    )
    session.add(
        ScanJob(
            type='normal',
            municipality_id=adlikon.id,
            delivery_number=2,
            dispatch_date=date(2019, 1, 10),
            dispatch_boxes=2,
            dispatch_tax_forms_current_year=5,
            dispatch_tax_forms_last_year=5,
            dispatch_tax_forms_older=0,
            dispatch_single_documents=2,
            dispatch_cantonal_tax_office=0,
            dispatch_cantonal_scan_center=0,
            return_date=date(2019, 2, 2),
            return_boxes=2,
            return_tax_forms_current_year=5,
            return_tax_forms_last_year=5,
            return_tax_forms_older=0,
            return_single_documents=2,
            return_unscanned_tax_forms_current_year=0,
            return_unscanned_tax_forms_last_year=0,
            return_unscanned_tax_forms_older=0,
            return_unscanned_single_documents=0,
        )
    )
    session.add(
        ScanJob(
            type='normal',
            municipality_id=aesch.id,
            delivery_number=3,
            dispatch_date=date(2019, 1, 7),
            dispatch_boxes=1,
            dispatch_tax_forms_current_year=10,
            dispatch_tax_forms_last_year=10,
            dispatch_tax_forms_older=10,
            dispatch_single_documents=10,
            dispatch_cantonal_tax_office=1,
            dispatch_cantonal_scan_center=1,
            return_date=date(2019, 1, 10),
            return_boxes=1,
            return_tax_forms_current_year=7,
            return_tax_forms_last_year=7,
            return_tax_forms_older=7,
            return_single_documents=7,
            return_unscanned_tax_forms_current_year=3,
            return_unscanned_tax_forms_last_year=3,
            return_unscanned_tax_forms_older=3,
            return_unscanned_single_documents=3,
        )
    )
    session.flush()

    with freeze_time("2019-12-31 08:07:06"):
        invoice = Invoice(session)

        def export():
            file = StringIO()
            invoice.export(file)
            file.seek(0)
            return file.read()

        # All
        invoice.municipality_id = None
        invoice.from_date = None
        invoice.to_date = None
        invoice.cs2_user = '123456'
        invoice.subject = 'Rechnungen'
        invoice.accounting_unit = '99999'
        invoice.revenue_account = '987654321'
        assert export() == (
            '201912311;2019-12-31;08.07.06;'
            '08882255;'
            '00001;'
            '08882255;'
            'Rechnungen;'
            '00001;001;'
            '2019-12-31;2019-12-31;2019-12-31;'
            '08882255;'
            '+00000000000048000;'
            'Lieferscheinnummer 1;'
            '+00000000070000000;+00000000070000000;'
            '1;'
            '2019-12-31;'
            'Finkenweg;'
            '123456;'
            '000;'
            '99999;'
            '987654321'
            '\r\n'
        ) + (
            '201912311;2019-12-31;08.07.06;'
            '08882255;'
            '00002;'
            '08882255;'
            'Rechnungen;'
            '00002;002;'
            '2019-12-31;2019-12-31;2019-12-31;'
            '08882255;'
            '+00000000000010000;'
            'Lieferscheinnummer 2;'
            '+00000000070000000;+00000000070000000;'
            '1;'
            '2019-12-31;'
            'Finkenweg;'
            '123456;'
            '000;'
            '99999;'
            '987654321'
            '\r\n'
        ) + (
            '201912312;2019-12-31;08.07.06;'
            '09993344;'
            '00001;'
            '09993344;'
            'Rechnungen;'
            '00001;001;'
            '2019-12-31;2019-12-31;2019-12-31;'
            '09993344;'
            '+00000000000012000;'
            'Lieferscheinnummer 3;'
            '+00000000085000000;+00000000085000000;'
            '1;'
            '2019-12-31;'
            'Meisenweg;'
            '123456;'
            '000;'
            '99999;'
            '987654321'
            '\r\n'
        )

        # Filter
        invoice.municipality_id = adlikon.id
        invoice.from_date = date(2019, 1, 1)
        invoice.to_date = date(2019, 1, 7)
        invoice.cs2_user = '123456'
        invoice.subject = 'Rechnungen 1.1-7.1'
        invoice.accounting_unit = '99999'
        invoice.revenue_account = '987654321'
        assert export() == ''

        invoice.from_date = date(2019, 1, 7)
        invoice.to_date = date(2019, 1, 14)
        assert export() == (
            '201912311;2019-12-31;08.07.06;'
            '08882255;'
            '00001;'
            '08882255;'
            'Rechnungen 1.1-7.1;'
            '00001;001;'
            '2019-12-31;2019-12-31;2019-12-31;'
            '08882255;'
            '+00000000000010000;'
            'Lieferscheinnummer 2;'
            '+00000000070000000;+00000000070000000;'
            '1;'
            '2019-12-31;'
            'Finkenweg;'
            '123456;'
            '000;'
            '99999;'
            '987654321'
            '\r\n'
        )


def test_user_manual(wtfs_app):
    user_manual = UserManual(wtfs_app)
    assert user_manual.filename == 'user_manual.pdf'
    assert user_manual.content_type == 'application/pdf'

    assert not user_manual.exists
    assert user_manual.pdf is None
    assert user_manual.content_length is None

    user_manual.pdf = b'Test'

    assert user_manual.exists
    assert user_manual.pdf == b'Test'
    assert user_manual.content_length == 4

    del user_manual.pdf

    assert not user_manual.exists
    assert user_manual.pdf is None
    assert user_manual.content_length is None
