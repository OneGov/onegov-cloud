from datetime import date
from onegov.user import UserGroup
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import PickupDate
from onegov.wtfs.models import Principal


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
