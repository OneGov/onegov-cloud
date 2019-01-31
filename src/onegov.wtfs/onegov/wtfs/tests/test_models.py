from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Principal
from onegov.user import UserGroup


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
    assert municipality.group is None

    session.add(UserGroup(name='Benutzer'))
    session.flush()

    group = session.query(UserGroup).one()
    assert group.municipality is None

    municipality.group_id = group.id
    session.flush()
    session.expire_all()

    assert municipality.group == group
    assert group.municipality == municipality
