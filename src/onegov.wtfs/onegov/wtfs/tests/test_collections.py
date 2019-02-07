from datetime import date
from onegov.wtfs.collections import MunicipalityCollection


def test_municipalities(session):
    municipalities = MunicipalityCollection(session)
    municipalities.add(name='Winterthur', bfs_number=230)
    municipalities.add(name='Adlikon', bfs_number=21)

    assert [(m.name, m.bfs_number) for m in municipalities.query()] == [
        ('Adlikon', 21),
        ('Winterthur', 230)
    ]

    # Import data
    data = {
        21: {
            'name': 'Adikon',
            'dates': [date(2019, 1, 1), date(2019, 1, 7)]
        },
        211: {
            'name': 'Altikon',
            'dates': [date(2019, 1, 2), date(2019, 1, 8)]
        },
        241: {
            'name': 'Aesch',
            'dates': [date(2019, 1, 3), date(2019, 1, 9)]
        },
        230: {
            'name': 'Winterthur',
            'dates': [date(2019, 1, 4), date(2019, 1, 10)]
        }
    }
    municipalities.import_data(data)

    assert [
        (m.name, m.bfs_number, [d.date for d in m.pickup_dates])
        for m in municipalities.query()
    ] == [
        ('Adikon', 21, [date(2019, 1, 1), date(2019, 1, 7)]),
        ('Aesch', 241, [date(2019, 1, 3), date(2019, 1, 9)]),
        ('Altikon', 211, [date(2019, 1, 2), date(2019, 1, 8)]),
        ('Winterthur', 230, [date(2019, 1, 4), date(2019, 1, 10)])
    ]

    data = {
        241: {
            'name': 'Aesch',
            'dates': [date(2019, 1, 9), date(2019, 1, 8)]
        },
        230: {
            'name': 'Winterthur',
            'dates': []
        }
    }
    municipalities.import_data(data)
    assert [
        (m.name, m.bfs_number, [d.date for d in m.pickup_dates])
        for m in municipalities.query()
    ] == [
        ('Adikon', 21, [date(2019, 1, 1), date(2019, 1, 7)]),
        ('Aesch', 241, [date(2019, 1, 3), date(2019, 1, 8), date(2019, 1, 9)]),
        ('Altikon', 211, [date(2019, 1, 2), date(2019, 1, 8)]),
        ('Winterthur', 230, [date(2019, 1, 4), date(2019, 1, 10)])
    ]
