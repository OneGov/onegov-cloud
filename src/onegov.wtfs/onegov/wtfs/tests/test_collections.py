from datetime import date
from onegov.user import UserGroupCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.collections import ScanJobCollection


def test_municipalities(session):
    groups = UserGroupCollection(session)

    municipalities = MunicipalityCollection(session)
    municipalities.add(
        name='Winterthur',
        bfs_number=230,
        group_id=groups.add(name='Winterthur').id
    )
    municipalities.add(
        name='Adlikon',
        bfs_number=21,
        group_id=groups.add(name='Adlikon').id
    )

    assert [(m.name, m.bfs_number) for m in municipalities.query()] == [
        ('Adlikon', 21),
        ('Winterthur', 230)
    ]

    # Import data
    data = {
        21: {'dates': [date(2019, 1, 1), date(2019, 1, 7)]},
        241: {'dates': [date(2019, 1, 2), date(2019, 1, 8)]},
        230: {'dates': [date(2019, 1, 4), date(2019, 1, 10)]}
    }
    municipalities.import_data(data)
    assert [
        (m.bfs_number, [d.date for d in m.pickup_dates])
        for m in municipalities.query()
    ] == [
        (21, [date(2019, 1, 1), date(2019, 1, 7)]),
        (230, [date(2019, 1, 4), date(2019, 1, 10)])
    ]

    municipalities.add(
        name='Aesch',
        bfs_number=241,
        group_id=groups.add(name='Aesch').id
    )
    data = {
        21: {'dates': [date(2019, 1, 7), date(2019, 1, 8)]},
        241: {'dates': [date(2019, 1, 2), date(2019, 1, 8)]},
        230: {'dates': []}
    }
    municipalities.import_data(data)
    assert [
        (m.bfs_number, [d.date for d in m.pickup_dates])
        for m in municipalities.query()
    ] == [
        (21, [date(2019, 1, 1), date(2019, 1, 7), date(2019, 1, 8)]),
        (241, [date(2019, 1, 2), date(2019, 1, 8)]),
        (230, [date(2019, 1, 4), date(2019, 1, 10)])
    ]


def test_scan_jobs(session):
    groups = UserGroupCollection(session)
    group = groups.add(name='Winterthur')

    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(
        name='Winterthur', bfs_number=230, group_id=group.id
    )

    scan_jobs = ScanJobCollection(session)
    for day in (2, 1, 4, 3):
        scan_jobs.add(
            type='normal',
            group_id=group.id,
            municipality_id=municipality.id,
            dispatch_date=date(2019, 1, day)
        )

    assert [s.dispatch_date.day for s in scan_jobs.query()] == [1, 2, 3, 4]
