from datetime import date
from decimal import Decimal

from onegov.core.utils import Bunch
from onegov.pas.models import (
    Party,
    Parliamentarian,
    ParliamentarianRole,
    RateSet,
    Commission,
    SettlementRun,
    Attendence,
)


def test_settlement_export(session):
    # Create test data
    rate_set = RateSet(year=2024)
    rate_set.cost_of_living_adjustment = Decimal('5.0')  # 5% adjustment
    rate_set.plenary_none_president_halfday = 1000
    rate_set.plenary_none_member_halfday = 500
    session.add(rate_set)

    # Create two parties
    party_a = Party(name='Party A')
    party_b = Party(name='Party B')
    session.add_all([party_a, party_b])

    # Create commission
    commission = Commission(name='Test Commission', type='normal')
    session.add(commission)

    # Create parliamentarians with roles
    pres = Parliamentarian(first_name='Jane', last_name='President')
    pres_role = ParliamentarianRole(
        parliamentarian=pres,
        role='president',
        party=party_a,
        start=date(2024, 1, 1),
    )

    mem = Parliamentarian(first_name='John', last_name='Member')
    mem_role = ParliamentarianRole(
        parliamentarian=mem,
        role='member',
        party=party_b,
        start=date(2024, 1, 1),
    )

    session.add_all([pres, mem, pres_role, mem_role])

    # Create settlement run
    run = SettlementRun(
        name='Q1 2024',
        start=date(2024, 1, 1),
        end=date(2024, 3, 31),
        active=True,
    )
    session.add(run)

    # Create attendences
    attendences = [
        # President attendence (Party A)
        Attendence(
            parliamentarian=pres,
            date=date(2024, 1, 15),
            duration=240,  # 4 hours
            type='plenary',
        ),
        # Member attendence (Party B)
        Attendence(
            parliamentarian=mem,
            date=date(2024, 2, 15),
            duration=240,  # 4 hours
            type='plenary',
        ),
    ]
    session.add_all(attendences)
    session.flush()

    # Test party totals
    totals = Bunch(session=session)
