from onegov.wtfs.collections import MunicipalityCollection


def test_municipalities(session):
    municipalities = MunicipalityCollection(session)
    municipalities.add(name='Winterthur', bfs_number=230)
    municipalities.add(name='Adlikon', bfs_number=21)

    assert [(m.name, m.bfs_number) for m in municipalities.query()] == [
        ('Adlikon', 21),
        ('Winterthur', 230)
    ]
