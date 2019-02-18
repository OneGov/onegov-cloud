from datetime import date
from onegov.user import UserGroup
from onegov.wtfs.models import DailyList
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import PickupDate
from onegov.wtfs.models import Principal
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
            return_unscanned_tax_forms_current_year=13,
            return_unscanned_tax_forms_last_year=14,
            return_unscanned_tax_forms_older=15,
            return_unscanned_single_documents=16,
        )
    )
    session.flush()

    scan_job = session.query(ScanJob).one()
    assert scan_job.municipality == municipality
    assert scan_job.group == group
    assert scan_job.delivery_number == 1
    assert scan_job.title.interpolate() == 'Scan job 1: Winterthur, 01.01.2019'
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
    assert scan_job.return_unscanned_tax_forms_current_year == 13
    assert scan_job.return_unscanned_tax_forms_last_year == 14
    assert scan_job.return_unscanned_tax_forms_older == 15
    assert scan_job.return_unscanned_tax_forms == 13 + 14 + 15
    assert scan_job.return_unscanned_single_documents == 16
    assert scan_job.return_tax_forms_current_year == 9 + 13
    assert scan_job.return_tax_forms_last_year == 10 + 14
    assert scan_job.return_tax_forms_older == 11 + 15
    assert scan_job.return_tax_forms == 9 + 10 + 11 + 13 + 14 + 15
    assert scan_job.return_single_documents == 12 + 16

    assert municipality.scan_jobs.one() == scan_job
    assert group.scan_jobs.one() == scan_job


def test_daily_list(session):
    daily_list = DailyList(session, date_=date.today())
    assert daily_list.jobs.all() == []
    assert daily_list.total == (0, 0, 0, 0)

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
                    return_date=job[4],
                    return_boxes=job[5],
                )
            )
        session.flush()
    session.flush()

    daily_list = DailyList(session, date_=date(2019, 1, 1))
    assert daily_list.jobs.all() == [
        ('Adlikon', 1, 2, 3, 0),
        ('Aesch', 1, 2, 3, 0)
    ]
    assert daily_list.total == (2, 4, 6, 0)

    daily_list = DailyList(session, date_=date(2019, 1, 2))
    assert daily_list.jobs.all() == [
        ('Adlikon', 3, 2, 1, 4),
        ('Aesch', 0, 0, 0, 4),
        ('Altikon', 1, 2, 3, 4),
        ('Andelfingen', 1, 2, 3, 0)
    ]
    assert daily_list.total == (5, 6, 7, 12)

    daily_list = DailyList(session, date_=date(2019, 1, 3))
    assert daily_list.jobs.all() == [
        ('Adlikon', 0, 0, 0, 1),
        ('Aesch', 0, 10, 0, 0)
    ]
    assert daily_list.total == (0, 10, 0, 1)

    daily_list = DailyList(session, date_=date(2019, 1, 4))
    assert daily_list.jobs.all() == [
        ('Aesch', 0, 0, 0, 0),
        ('Andelfingen', 0, 0, 0, 4)
    ]
    assert daily_list.total == (0, 0, 0, 4)

    daily_list = DailyList(session, date_=date(2019, 1, 5))
    assert daily_list.jobs.all() == []
    assert daily_list.total == (0, 0, 0, 0)
