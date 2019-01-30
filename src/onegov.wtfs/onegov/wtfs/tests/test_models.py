from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Principal


def test_principal():
    principal = Principal()
    assert principal


def test_municipality(session):
    session.add(
        Municipality(
            name='Winterthur',
            bfs_number=230,
        )
    )
    session.flush()

    municipality = session.query(Municipality).one()
    assert municipality.name == 'Winterthur'
    assert municipality.bfs_number == 230
