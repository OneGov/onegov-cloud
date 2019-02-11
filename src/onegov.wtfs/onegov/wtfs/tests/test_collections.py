from datetime import date
from onegov.user import UserGroupCollection
from onegov.wtfs.collections import MunicipalityCollection


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
