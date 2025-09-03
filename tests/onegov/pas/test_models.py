from freezegun import freeze_time
from datetime import date
from onegov.core.utils import Bunch
from onegov.pas.models import (
    Attendence,
    Change,
    LegislativePeriod,
    PASCommission,
    PASCommissionMembership,
    PASParliamentarian,
    PASParliamentarianRole,
    PASParliamentaryGroup,
    Party,
    RateSet,
    SettlementRun
)


@freeze_time('2022-06-06')
def test_models(session):
    rate_set = RateSet(year=2022)
    legislative_period = LegislativePeriod(
        name='2022-2024',
        start=date(2022, 1, 1),
        end=date(2022, 12, 31)
    )
    settlement_run = SettlementRun(
        name='2022-1',
        start=date(2022, 1, 1),
        end=date(2022, 3, 31),
        active=True
    )
    parliamentary_group = PASParliamentaryGroup(name='Group')
    party = Party(name='Party')
    commission = PASCommission(
        name='Official Commission',
        type='official'
    )
    parliamentarian = PASParliamentarian(
        first_name='First',
        last_name='Last',
        gender='female',
        shipping_method='plus'
    )
    session.add(rate_set)
    session.add(legislative_period)
    session.add(settlement_run)
    session.add(parliamentary_group)
    session.add(party)
    session.add(commission)
    session.add(parliamentarian)
    session.flush()

    parliamentarian_role = PASParliamentarianRole(
        parliamentarian_id=parliamentarian.id,
        role='vice_president',
        party_id=party.id,
        party_role='media_manager',
        parliamentary_group_id=parliamentary_group.id,
        parliamentary_group_role='vote_counter'
    )
    commission_membership = PASCommissionMembership(
        role='president',
        commission_id=commission.id,
        parliamentarian_id=parliamentarian.id
    )
    attendence = Attendence(
        date=date(2022, 1, 1),
        duration=30,
        type='commission',
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id
    )
    session.add(parliamentarian_role)
    session.add(commission_membership)
    session.add(attendence)
    session.flush()

    change = Change.add(
        request=Bunch(
            current_username='user@example.org',
            current_user=Bunch(title='User'),
            session=session
        ),
        action='add',
        attendence=attendence
    )
    session.add(change)
    session.flush()

    # labels
    assert attendence.type_label == 'Commission meeting'
    assert commission.type_label == 'official mission'
    assert commission_membership.role_label == 'President'
    assert parliamentarian.gender_label == 'female'
    assert parliamentarian.shipping_method_label == 'A mail plus'
    assert parliamentarian_role.role_label == 'Vice president'
    assert parliamentarian_role.party_role_label == 'Media Manager'
    assert parliamentarian_role.parliamentary_group_role_label == \
        'Vote counter'
    assert change.action_label == 'Attendence added'

    # relationships
    assert commission.memberships == [commission_membership]
    assert commission.attendences == [attendence]
    assert parliamentarian.roles == [parliamentarian_role]
    assert parliamentarian.commission_memberships == [commission_membership]
    assert parliamentarian.attendences == [attendence]
    assert parliamentary_group.roles == [parliamentarian_role]
    assert party.roles == [parliamentarian_role]
    assert change.attendence == attendence
    assert change.parliamentarian == parliamentarian
    assert change.commission == commission

    # properties
    assert parliamentarian.title == 'First Last'
    assert change.user == 'User (user@example.org)'
    assert change.date == date(2022, 1, 1)

    # ... parliamentarian.active
    assert parliamentarian.active is True
    parliamentarian_role.end = date(2022, 5, 5)
    commission_membership.end = date(2022, 5, 5)
    assert parliamentarian.active is False
    parliamentarian.roles = []
    parliamentarian.commission_memberships = []
    assert parliamentarian.active is True

    # commission.end_observer
    assert parliamentarian.active is True
    commission.end = date(2022, 5, 5)
    session.flush()
    assert commission_membership.end == date(2022, 5, 5)
