from datetime import date
from decimal import Decimal
import transaction
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
from onegov.pas.views.settlement_run import generate_settlement_pdf,\
    _get_commission_settlement_data, _get_commission_totals


def test_business_rules_export_data(session):

    with transaction.manager:
        rate_set = RateSet(year=2024)
        rate_set.cost_of_living_adjustment = Decimal('5.0')  # 5% adjustment
        rate_set.plenary_none_president_halfday = 1000
        rate_set.plenary_none_member_halfday = 500
        rate_set.commission_normal_president_initial = 300
        rate_set.commission_normal_member_initial = 200
        rate_set.study_normal_president_halfhour = 100
        rate_set.study_normal_member_halfhour = 80
        session.add(rate_set)

        # Create parties
        party_a = Party(name='Party A')
        party_b = Party(name='Party B')
        session.add_all([party_a, party_b])

        # Create commissions
        commission_a = Commission(name='Commission A', type='normal')
        commission_b = Commission(name='Commission B', type='normal')
        session.add_all([commission_a, commission_b])

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
        run_id = run.id

        # Create various types of attendences
        attendences = [
            # Plenary attendences
            Attendence(
                parliamentarian=pres,
                date=date(2024, 1, 15),
                duration=240,  # 4 hours
                type='plenary',
            ),
            Attendence(
                parliamentarian=mem,
                date=date(2024, 2, 15),
                duration=240,  # 4 hours
                type='plenary',
            ),
            # Commission attendences
            Attendence(
                parliamentarian=pres,
                date=date(2024, 1, 20),
                duration=180,  # 3 hours
                type='commission',
                commission=commission_a,
            ),
            Attendence(
                parliamentarian=mem,
                date=date(2024, 2, 20),
                duration=180,  # 3 hours
                type='commission',
                commission=commission_a,
            ),
            # Study attendences
            Attendence(
                parliamentarian=pres,
                date=date(2024, 1, 25),
                duration=60,  # 1 hour
                type='study',
                commission=commission_a,
            ),
            Attendence(
                parliamentarian=mem,
                date=date(2024, 2, 25),
                duration=60,  # 1 hour
                type='study',
                commission=commission_a,
            ),
        ]
        session.add_all(attendences)
        session.flush()
        transaction.commit()


    # Test commission-specific exports

    # Let's write this test

    request = Bunch(session=session, translate=lambda x: str(x))
    settlement_data = _get_commission_settlement_data(
        run, request, commission_b
    )
    totals = _get_commission_totals(run, request, commission_b)
    breakpoint()

    # Test parliamentarian-specific exports

    # Test party-specific exports




# # fixme: complete writing thi test
# def test_settlement_export(session):
#     # Create test data
#     rate_set = RateSet(year=2024)
#     rate_set.cost_of_living_adjustment = Decimal('5.0')  # 5% adjustment
#     rate_set.plenary_none_president_halfday = 1000
#     rate_set.plenary_none_member_halfday = 500
#     session.add(rate_set)
#
#     # Create two parties
#     party_a = Party(name='Party A')
#     party_b = Party(name='Party B')
#     session.add_all([party_a, party_b])
#
#     # Create commission
#     commission = Commission(name='Test Commission', type='normal')
#     session.add(commission)
#
#     # Create parliamentarians with roles
#     pres = Parliamentarian(first_name='Jane', last_name='President')
#     pres_role = ParliamentarianRole(
#         parliamentarian=pres,
#         role='president',
#         party=party_a,
#         start=date(2024, 1, 1),
#     )
#
#     mem = Parliamentarian(first_name='John', last_name='Member')
#     mem_role = ParliamentarianRole(
#         parliamentarian=mem,
#         role='member',
#         party=party_b,
#         start=date(2024, 1, 1),
#     )
#
#     session.add_all([pres, mem, pres_role, mem_role])
#
#     # Create settlement run
#     run = SettlementRun(
#         name='Q1 2024',
#         start=date(2024, 1, 1),
#         end=date(2024, 3, 31),
#         active=True,
#     )
#     session.add(run)
#
#     # Create attendences
#     attendences = [
#         # President attendence (Party A)
#         Attendence(
#             parliamentarian=pres,
#             date=date(2024, 1, 15),
#             duration=240,  # 4 hours
#             type='plenary',
#         ),
#         # Member attendence (Party B)
#         Attendence(
#             parliamentarian=mem,
#             date=date(2024, 2, 15),
#             duration=240,  # 4 hours
#             type='plenary',
#         ),
#     ]
#     session.add_all(attendences)
#     session.flush()
#
#     # Test party totals
#     totals = Bunch(session=session)
