from datetime import date
from onegov.user import UserGroup
from onegov.wtfs.models import DailyListBoxes
from onegov.wtfs.models import DailyListBoxesAndForms
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Notification
from onegov.wtfs.models import PickupDate
from onegov.wtfs.models import Principal
from onegov.wtfs.models import ReportBoxes
from onegov.wtfs.models import ReportBoxesAndForms
from onegov.wtfs.models import ReportFormsByMunicipality
from onegov.wtfs.models import ScanJob
from uuid import uuid4


def test_principal():
    principal = Principal()
    assert principal


def test_municipality(session):
    session.add(UserGroup(name='Benutzer'))
    session.flush()
    group = session.query(UserGroup).one()

    session.add(
        Municipality(
            name='Winterthur',
            bfs_number=230,
            group_id=group.id
        )
    )
    session.flush()

    municipality = session.query(Municipality).one()
    assert municipality.name == 'Winterthur'
    assert municipality.bfs_number == 230
    assert municipality.group == group
    assert group.municipality == municipality
    assert not municipality.has_data

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


def test_scan_job(session):
    session.add(UserGroup(name='Benutzer'))
    session.flush()
    group = session.query(UserGroup).one()

    session.add(
        Municipality(name='Winterthur', bfs_number=230, group_id=group.id)
    )
    session.flush()
    municipality = session.query(Municipality).one()

    session.add(
        ScanJob(
            type='normal',
            group_id=group.id,
            municipality_id=municipality.id,
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
            return_scanned_tax_forms_current_year=9,
            return_scanned_tax_forms_last_year=10,
            return_scanned_tax_forms_older=11,
            return_scanned_single_documents=12,
            return_unscanned_tax_forms_current_year=16,
            return_unscanned_tax_forms_last_year=15,
            return_unscanned_tax_forms_older=14,
            return_unscanned_single_documents=13,
        )
    )
    session.flush()

    scan_job = session.query(ScanJob).one()
    assert scan_job.municipality == municipality
    assert scan_job.group == group
    assert scan_job.delivery_number == 1
    assert scan_job.title.interpolate() == 'Scan job no. 1'
    assert scan_job.type == 'normal'
    assert scan_job.group_id == group.id
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
    assert scan_job.return_scanned_tax_forms_current_year == 9
    assert scan_job.return_scanned_tax_forms_last_year == 10
    assert scan_job.return_scanned_tax_forms_older == 11
    assert scan_job.return_scanned_tax_forms == 9 + 10 + 11
    assert scan_job.return_scanned_single_documents == 12
    assert scan_job.return_unscanned_tax_forms_current_year == 16
    assert scan_job.return_unscanned_tax_forms_last_year == 15
    assert scan_job.return_unscanned_tax_forms_older == 14
    assert scan_job.return_unscanned_tax_forms == 16 + 15 + 14
    assert scan_job.return_unscanned_single_documents == 13
    assert scan_job.return_tax_forms_current_year == 9 - 16
    assert scan_job.return_tax_forms_last_year == 10 - 15
    assert scan_job.return_tax_forms_older == 11 - 14
    assert scan_job.return_tax_forms == 9 + 10 + 11 - 16 - 15 - 14
    assert scan_job.return_single_documents == 12 - 13

    assert municipality.scan_jobs.one() == scan_job
    assert group.scan_jobs.one() == scan_job
    assert municipality.has_data


def add_report_data(session):
    data = {
        'Adlikon': {
            'municipality_id': uuid4(),
            'group_id': uuid4(),
            'bfs_number': 21,
            'jobs': [
                [date(2019, 1, 1), 1, 2, 3, date(2019, 1, 2), 4],
                [date(2019, 1, 2), 3, 2, 1, date(2019, 1, 3), 1],
            ]
        },
        'Aesch': {
            'municipality_id': uuid4(),
            'group_id': uuid4(),
            'bfs_number': 241,
            'jobs': [
                [date(2019, 1, 1), 1, 2, 3, date(2019, 1, 2), 4],
                [date(2019, 1, 3), 0, 10, None, date(2019, 1, 4), None],
            ]
        },
        'Altikon': {
            'municipality_id': uuid4(),
            'group_id': uuid4(),
            'bfs_number': 211,
            'jobs': [
                [date(2019, 1, 2), 1, 2, 3, date(2019, 1, 2), 4],
            ]
        },
        'Andelfingen': {
            'municipality_id': uuid4(),
            'group_id': uuid4(),
            'bfs_number': 30,
            'jobs': [
                [date(2019, 1, 2), 1, 2, 3, date(2019, 1, 4), 4],
            ]
        },
    }

    for name, values in data.items():
        session.add(UserGroup(
            name=name,
            id=values['group_id']
        ))
        session.add(Municipality(
            name=name,
            id=values['municipality_id'],
            bfs_number=values['bfs_number'],
            group_id=values['group_id'])
        )
        for job in values['jobs']:
            session.add(
                ScanJob(
                    type='normal',
                    group_id=values['group_id'],
                    municipality_id=values['municipality_id'],
                    dispatch_date=job[0],
                    dispatch_boxes=job[1],
                    dispatch_cantonal_tax_office=job[2],
                    dispatch_cantonal_scan_center=job[3],
                    dispatch_tax_forms_older=job[1],
                    dispatch_tax_forms_last_year=job[2],
                    dispatch_tax_forms_current_year=job[3],
                    dispatch_single_documents=job[5],
                    return_date=job[4],
                    return_boxes=job[5],
                )
            )
        session.flush()
    session.flush()


def test_daily_list_boxes(session):
    daily_list = DailyListBoxes(session, date_=date.today())
    assert daily_list.query.all() == []
    assert daily_list.total == (0, 0, 0, 0)

    add_report_data(session)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 1))
    assert daily_list.query.all() == [
        ('Adlikon', 21, 1, 2, 3, 0),
        ('Aesch', 241, 1, 2, 3, 0)
    ]
    assert daily_list.total == (2, 4, 6, 0)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 2))
    assert daily_list.query.all() == [
        ('Adlikon', 21, 3, 2, 1, 4),
        ('Aesch', 241, 0, 0, 0, 4),
        ('Altikon', 211, 1, 2, 3, 4),
        ('Andelfingen', 30, 1, 2, 3, 0)
    ]
    assert daily_list.total == (5, 6, 7, 12)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 3))
    assert daily_list.query.all() == [
        ('Adlikon', 21, 0, 0, 0, 1),
        ('Aesch', 241, 0, 10, 0, 0)
    ]
    assert daily_list.total == (0, 10, 0, 1)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 4))
    assert daily_list.query.all() == [
        ('Aesch', 241, 0, 0, 0, 0),
        ('Andelfingen', 30, 0, 0, 0, 4)
    ]
    assert daily_list.total == (0, 0, 0, 4)

    daily_list = DailyListBoxes(session, date_=date(2019, 1, 5))
    assert daily_list.query.all() == []
    assert daily_list.total == (0, 0, 0, 0)


def test_daily_list_boxes_and_forms(session):
    daily_list = DailyListBoxesAndForms(session, date_=date.today())
    assert daily_list.query.all() == []
    assert daily_list.total == (0, 0, 0, 0, 0, 0, 0)

    add_report_data(session)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 1))
    assert daily_list.query.all() == [
        ('Adlikon', 21, 1, 1, 2, 3, 4, 2, 3),
        ('Aesch', 241, 1, 1, 2, 3, 4, 2, 3)
    ]
    assert daily_list.total == (2, 2, 4, 6, 8, 4, 6)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 2))

    assert daily_list.query.all() == [
        ('Adlikon', 21, 3, 3, 2, 1, 1, 2, 1),
        ('Aesch', 241, 0, 0, 0, 0, 0, 0, 0),
        ('Altikon', 211, 1, 1, 2, 3, 4, 2, 3),
        ('Andelfingen', 30, 1, 1, 2, 3, 4, 2, 3)
    ]
    assert daily_list.total == (5, 5, 6, 7, 9, 6, 7)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 3))
    assert daily_list.query.all() == [
        ('Adlikon', 21, 0, 0, 0, 0, 0, 0, 0),
        ('Aesch', 241, 0, 0, 10, 0, 0, 10, 0)
    ]
    assert daily_list.total == (0, 0, 10, 0, 0, 10, 0)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 4))
    assert daily_list.query.all() == [
        ('Aesch', 241, 0, 0, 0, 0, 0, 0, 0),
        ('Andelfingen', 30, 0, 0, 0, 0, 0, 0, 0)
    ]
    assert daily_list.total == (0, 0, 0, 0, 0, 0, 0)

    daily_list = DailyListBoxesAndForms(session, date_=date(2019, 1, 5))
    assert daily_list.query.all() == []
    assert daily_list.total == (0, 0, 0, 0, 0, 0, 0)


def test_report_boxes(session):
    def _report(start, end):
        return ReportBoxes(session, start=start, end=end)

    report = _report(date.today(), date.today())
    assert report.query.all() == []
    assert report.total == (0, 0, 0, 0)

    add_report_data(session)

    report = _report(date(2019, 1, 1), date(2019, 1, 1))
    assert report.query.all() == [
        ('Adlikon', 21, 1, 2, 3, 0),
        ('Aesch', 241, 1, 2, 3, 0)
    ]
    assert report.total == (2, 4, 6, 0)

    report = _report(date(2019, 1, 2), date(2019, 1, 3))
    assert report.query.all() == [
        ('Adlikon', 21, 3, 2, 1, 5),
        ('Aesch', 241, 0, 10, 0, 4),
        ('Altikon', 211, 1, 2, 3, 4),
        ('Andelfingen', 30, 1, 2, 3, 0)
    ]
    assert report.total == (5, 16, 7, 13)

    report = _report(date(2019, 1, 4), date(2019, 1, 5))
    assert report.query.all() == [
        ('Aesch', 241, 0, 0, 0, 0),
        ('Andelfingen', 30, 0, 0, 0, 4)
    ]
    assert report.total == (0, 0, 0, 4)


def test_report_boxes_and_forms(session):
    def _report(start, end):
        return ReportBoxesAndForms(session, start=start, end=end)

    report = _report(date.today(), date.today())
    assert report.query.all() == []
    assert report.total == (0, 0, 0, 0, 0)

    add_report_data(session)

    report = _report(date(2019, 1, 1), date(2019, 1, 1))
    assert report.query.all() == [
        ('Adlikon', 21, 1, 2, 3, 4, 0),
        ('Aesch', 241, 1, 2, 3, 4, 0)
    ]
    assert report.total == (2, 4, 6, 8, 0)

    report = _report(date(2019, 1, 2), date(2019, 1, 3))
    assert report.query.all() == [
        ('Adlikon', 21, 3, 2, 1, 1, 5),
        ('Aesch', 241, 0, 10, 0, 0, 4),
        ('Altikon', 211, 1, 2, 3, 4, 4),
        ('Andelfingen', 30, 1, 2, 3, 4, 0)
    ]
    assert report.total == (5, 16, 7, 9, 13)

    report = _report(date(2019, 1, 4), date(2019, 1, 5))
    assert report.query.all() == [
        ('Aesch', 241, 0, 0, 0, 0, 0),
        ('Andelfingen', 30, 0, 0, 0, 0, 4)
    ]
    assert report.total == (0, 0, 0, 0, 4)


def test_report_forms_by_municipality(session):
    def _report(start, end, municipality):
        query = session.query(Municipality).filter_by(name=municipality)
        return ReportFormsByMunicipality(
            session, start=start, end=end, municipality_id=query.one().id
        )

    add_report_data(session)

    report = _report(date(2019, 1, 1), date(2019, 1, 1), 'Adlikon')
    assert report.query.all() == [('Adlikon', 21, 1, 2, 3)]
    report = _report(date(2019, 1, 1), date(2019, 1, 1), 'Aesch')
    assert report.query.all() == [('Aesch', 241, 1, 2, 3)]

    report = _report(date(2019, 1, 2), date(2019, 1, 3), 'Adlikon')
    assert report.query.all() == [('Adlikon', 21, 3, 2, 1)]
    report = _report(date(2019, 1, 2), date(2019, 1, 3), 'Aesch')
    assert report.query.all() == [('Aesch', 241, 0, 10, 0)]
    report = _report(date(2019, 1, 2), date(2019, 1, 3), 'Altikon')
    assert report.query.all() == [('Altikon', 211, 1, 2, 3)]
    report = _report(date(2019, 1, 2), date(2019, 1, 3), 'Andelfingen')
    assert report.query.all() == [('Andelfingen', 30, 1, 2, 3)]

    report = _report(date(2019, 1, 4), date(2019, 1, 5), 'Aesch')
    assert report.query.all() == [('Aesch', 241, 0, 0, 0)]
    report = _report(date(2019, 1, 4), date(2019, 1, 5), 'Andelfingen')
    assert report.query.all() == [('Andelfingen', 30, 0, 0, 0)]


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
