from freezegun import freeze_time
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import ChangeCollection
from onegov.pas.collections import CommissionCollection
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.collections import ParliamentarianRoleCollection
from onegov.pas.collections import ParliamentaryGroupCollection
from onegov.pas.collections import PartyCollection
from onegov.pas.collections import RateSetCollection
from onegov.pas.collections import SettlementRunCollection
from datetime import date


def test_attendence_collection(session):
    parliamentarians = ParliamentarianCollection(session)
    parliamentarian = parliamentarians.add(
        first_name='a',
        last_name='b'
    )

    attendences = AttendenceCollection(session)
    attendences.add(
        date=date(2024, 1, 1),
        duration=1,
        type='plenary',
        parliamentarian_id=parliamentarian.id
    )
    attendences.add(
        date=date(2024, 1, 2),
        duration=1,
        type='plenary',
        parliamentarian_id=parliamentarian.id
    )

    # ordering
    assert [a.date.day for a in attendences.query()] == [2, 1]


def test_change_collection(session):
    changes = ChangeCollection(session)
    changes.add(action='add', model='attendence')
    changes.add(action='edit', model='attendence')

    # ordering
    assert [c.action for c in changes.query()] == ['edit', 'add']


@freeze_time('2024-01-01')
def test_commission_collection(session):
    commissions = CommissionCollection(session)
    commissions.add(name='c')
    commissions.add(name='b', end=date(2025, 1, 1))
    commissions.add(name='a', end=date(2023, 1, 1))

    # ordering
    assert [c.name for c in commissions.query()] == ['a', 'b', 'c']

    # filtering
    assert commissions.for_filter(active=True).query().count() == 2
    assert commissions.for_filter(active=False).query().count() == 1


@freeze_time('2024-01-01')
def test_legiaslative_period_collection(session):
    periods = LegislativePeriodCollection(session)
    periods.add(name='b', start=date(2023, 1, 1), end=date(2025, 1, 1))
    periods.add(name='a', start=date(2021, 1, 1), end=date(2023, 1, 1))

    # ordering
    assert [c.name for c in periods.query()] == ['a', 'b']

    # filtering
    assert periods.for_filter(active=True).query().one().name == 'b'
    assert periods.for_filter(active=False).query().one().name == 'a'


@freeze_time('2024-01-01')
def test_parliamentarian_collection(session):
    parliamentarians = ParliamentarianCollection(session)
    a = parliamentarians.add(
        first_name='a',
        last_name='b'
    )
    b = parliamentarians.add(
        first_name='b',
        last_name='b'
    )
    parliamentarians.add(
        first_name='c',
        last_name='c'
    )

    roles = ParliamentarianRoleCollection(session)
    roles.add(parliamentarian_id=a.id)
    roles.add(parliamentarian_id=b.id, end=date(2023, 1, 1))

    # ordering
    assert [c.first_name for c in parliamentarians.query()] == ['a', 'b', 'c']

    # filtering
    assert parliamentarians.for_filter(active=True).query().count() == 2
    assert parliamentarians.for_filter(active=False).query().count() == 1


@freeze_time('2024-01-01')
def test_parliamentarian_group_collection(session):
    groups = ParliamentaryGroupCollection(session)
    groups.add(name='c')
    groups.add(name='b', end=date(2025, 1, 1))
    groups.add(name='a', end=date(2023, 1, 1))

    # ordering
    assert [c.name for c in groups.query()] == ['a', 'b', 'c']

    # filtering
    assert groups.for_filter(active=True).query().count() == 2
    assert groups.for_filter(active=False).query().count() == 1


@freeze_time('2024-01-01')
def test_party_collection(session):
    parties = PartyCollection(session)
    parties.add(name='c')
    parties.add(name='b', end=date(2025, 1, 1))
    parties.add(name='a', end=date(2023, 1, 1))

    # ordering
    assert [c.name for c in parties.query()] == ['a', 'b', 'c']

    # filtering
    assert parties.for_filter(active=True).query().count() == 2
    assert parties.for_filter(active=False).query().count() == 1


@freeze_time('2024-01-01')
def test_rate_set_collection(session):
    rates = RateSetCollection(session)
    rates.add(year=2022)
    rates.add(year=2023)
    rates.add(year=2024)

    # ordering
    assert [r.year for r in rates.query()] == [2024, 2023, 2022]

    # filtering
    assert rates.for_filter(active=True).query().count() == 1
    assert rates.for_filter(active=False).query().count() == 2


def test_settlement_run_collection(session):
    runs = SettlementRunCollection(session)
    runs.add(
        name='c',
        start=date(2022, 1, 1),
        end=date(2022, 2, 2),
        active=False
    )
    runs.add(
        name='b',
        start=date(2023, 1, 1),
        end=date(2023, 2, 2),
        active=False
    )
    runs.add(
        name='a',
        start=date(2024, 1, 1),
        end=date(2024, 2, 2),
        active=True
    )

    # ordering
    assert [r.name for r in runs.query()] == ['a', 'b', 'c']

    # filtering
    assert runs.for_filter(active=True).query().count() == 1
    assert runs.for_filter(active=False).query().count() == 2
