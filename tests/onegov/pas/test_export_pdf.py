from __future__ import annotations

import transaction

from datetime import date
from decimal import Decimal
from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import AttendenceCollection
from onegov.pas.export_single_parliamentarian import (
    generate_parliamentarian_settlement_pdf,
)
import onegov.pas.export_single_parliamentarian as pdf_export
from onegov.pas.views.pas_excel_export_nr_3_lohnart_fibu import (
    generate_fibu_export_rows,
)
from onegov.pas.models import (
    Party,
    PASParliamentarian,
    PASParliamentarianRole,
    RateSet,
    PASCommission,
    SettlementRun,
    Attendence,
    PASCommissionMembership,
)
from onegov.pas.models.presidential_allowance import (
    LOHNART_ALLOWANCE_TEXT,
    PresidentialAllowance,
)
import onegov.pas.views.settlement_run as settlement_run_views
from onegov.pas.views.settlement_run import _get_commission_settlement_data
from onegov.pas.views.settlement_run import _settlement_totals
from onegov.pas.views.settlement_run import generate_settlement_pdf
from onegov.town6.request import TownRequest
from unittest.mock import Mock
import pytest


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_parliamentarian_pdf_formats_hours_as_decimal(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rate_set = RateSet(
        year=2024,
        cost_of_living_adjustment=Decimal('21.935'),
        plenary_none_member_halfday=Decimal('43'),
    )
    settlement_run = SettlementRun(
        name='Q1 2024',
        start=date(2024, 1, 1),
        end=date(2024, 3, 31),
        active=True,
    )
    parliamentarian = PASParliamentarian(
        first_name='Jane',
        last_name='Member',
        gender='female',
    )
    session.add_all(
        [
            rate_set,
            settlement_run,
            parliamentarian,
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 1, 15),
                duration=205,
                type='plenary',
            ),
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 1, 16),
                duration=205,
                type='plenary',
            ),
        ]
    )
    session.flush()

    html = Mock()
    html.write_pdf.return_value = b'%PDF'
    html_factory = Mock(return_value=html)
    monkeypatch.setattr(pdf_export, 'HTML', html_factory)
    monkeypatch.setattr(pdf_export, 'CSS', Mock())
    monkeypatch.setattr(pdf_export, 'FontConfiguration', Mock())

    request = Mock(spec=TownRequest)
    request.session = session
    request.translate = lambda value: value

    result = generate_parliamentarian_settlement_pdf(
        settlement_run,
        request,
        parliamentarian,
    )

    assert result == b'%PDF'
    rendered_html = html_factory.call_args.kwargs['string']
    assert rendered_html.count('<td class="numeric">3.42</td>') == 2
    assert rendered_html.count('<td class="numeric">43.00</td>') == 2
    assert rendered_html.count('>104.90</td>') == 2

    fibu_rows = list(generate_fibu_export_rows(settlement_run, request))
    fibu_amounts = [row[12] for row in fibu_rows]
    assert all(isinstance(amount, Decimal) for amount in fibu_amounts)
    fibu_total = sum(
        (amount for amount in fibu_amounts if isinstance(amount, Decimal)),
        Decimal('0'),
    )
    assert fibu_total == Decimal('104.90')


def test_parliamentarian_settlement_calculations(session: Session) -> None:
    """Test the business logic for calculating parliamentarian settlements."""

    with transaction.manager:
        # Setup test data
        rate_set = RateSet(year=2024)
        rate_set.cost_of_living_adjustment = 5.0  # 5% adjustment

        # Set rates
        rate_set.plenary_none_president_halfday = 1000
        rate_set.plenary_none_member_halfday = 500
        rate_set.commission_normal_president_initial = 300
        rate_set.commission_normal_member_initial = 200
        rate_set.commission_normal_president_additional = 100
        rate_set.commission_normal_member_additional = 80
        rate_set.study_normal_president_halfhour = 100
        rate_set.study_normal_member_halfhour = 80
        session.add(rate_set)

        # Create parliamentarian with president role
        parliamentarian = PASParliamentarian(
            first_name='Jane',
            last_name='President',
            gender='female'
        )
        party = Party(name='Test Party')
        role = PASParliamentarianRole(
            parliamentarian=parliamentarian,
            role='president',
            party=party,
            start=date(2024, 1, 1),
        )
        session.add_all([parliamentarian, role, party])

        # Create commission
        commission = PASCommission(name='Test PASCommission', type='normal')
        session.add(commission)

        # Create various attendances to test different scenarios
        attendences = [
            # Plenary session (always counts as half day)
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 1, 15),
                duration=240,  # 4 hours - should still count as half day
                type='plenary'
            ),

            # Commission meetings
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 1, 20),
                duration=120,  # 2 hours - initial rate only
                type='commission',
                commission=commission
            ),
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 1, 21),
                duration=180,  # 3 hours - initial + additional rate
                type='commission',
                commission=commission
            ),

            # Study sessions
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 2, 1),
                duration=60,  # 1 hour
                type='study',
                commission=commission
            ),
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 2, 2),
                duration=90,  # 1.5 hours
                type='study',
                commission=commission
            )
        ]
        session.add_all(attendences)

        # Create settlement run
        run = SettlementRun(
            name='Q1 2024',
            start=date(2024, 1, 1),
            end=date(2024, 3, 31),
            active=True,
        )
        session.add(run)
        session.flush()
        transaction.commit()

    # Test individual rate calculations
    for attendence in AttendenceCollection(session).query():
        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=True,
            commission_type=(
                attendence.commission.type if attendence.commission else None
            ),
        )

        if attendence.type == 'plenary':
            # Plenary sessions: CHF always half day, but value shows actual hrs
            assert base_rate == Decimal('1000')
            # Actual duration was 240 minutes (4 hours)
            assert attendence.calculate_value() == Decimal('4.0')
        elif attendence.type == 'commission':
            if attendence.duration == 120:  # 2 hour meeting
                assert base_rate == Decimal('300')  # Initial rate only
                assert attendence.calculate_value() == Decimal('2.0')
            elif attendence.duration == 180:  # 3 hour meeting
                # Initial rate (300) + 2 additional half hours (2 * 100)
                assert base_rate == Decimal('500')
                assert attendence.calculate_value() == Decimal('3.0')
        elif attendence.type == 'study':
            if attendence.duration == 60:  # 1 hour
                # 2 half-hour periods at 100 each
                assert base_rate == Decimal('200')
                assert attendence.calculate_value() == Decimal('1.0')
            elif attendence.duration == 90:  # 1.5 hours
                # 3 half-hour periods at 100 each
                assert base_rate == Decimal('300')
                assert attendence.calculate_value() == Decimal('1.5')


    # Test total calculations for the settlement period
    session.expire_all()  # Ensure all instances are refreshed from the db
    attendences = AttendenceCollection(
        session,
        date_from=run.start,
        date_to=run.end,
        parliamentarian_id=str(parliamentarian.id)
    ).query().all()

    total_base = sum(
        calculate_rate(
            rate_set=rate_set,
            attendence_type=a.type,
            duration_minutes=int(a.duration),
            is_president=True,
            commission_type=a.commission.type if a.commission else None
        ) for a in attendences
    )

    # Expected calculations:
    # 1. Plenary (half day): 1000
    # 2. Commission (2h): 300
    # 3. Commission (3h): 500
    # 4. Study (1h): 200
    # 5. Study (1.5h): 300
    expected_base = Decimal('2300')
    assert total_base == expected_base

    # Test COLA calculations
    cola_amount = total_base * Decimal('0.05')  # 5% adjustment
    assert cola_amount == Decimal('115')

    final_total = total_base + cola_amount
    assert final_total == Decimal('2415')

def test_commission_export_one_member_one_president(session: Session) -> None:
    """Test commission export with one member and one president."""


    with transaction.manager:
        # Create rate set with actual current values
        rate_set = RateSet(year=2025)
        rate_set.cost_of_living_adjustment = 21.935

        rate_set.plenary_none_member_halfday = 184
        rate_set.shortest_all_member_halfhour = 26
        rate_set.study_normal_member_halfhour = 26
        rate_set.plenary_none_president_halfday = 307
        rate_set.shortest_all_president_halfhour = 26
        rate_set.study_intercantonal_member_hour = 86
        rate_set.study_normal_president_halfhour = 43
        rate_set.commission_normal_member_initial = 104
        rate_set.study_intercantonal_president_hour = 86
        rate_set.commission_normal_member_additional = 26
        rate_set.commission_normal_president_initial = 104
        rate_set.commission_normal_president_additional = 26
        rate_set.commission_intercantonal_member_halfday = 147
        rate_set.commission_intercantonal_president_halfday = 246
        session.add(rate_set)

        # Create commission
        commission = PASCommission(name='Test Commission', type='normal')
        session.add(commission)

        # Create parliamentarians
        president = PASParliamentarian(
            first_name='Anna',
            last_name='President',
            gender='female'
        )
        member = PASParliamentarian(
            first_name='Max',
            last_name='Member',
            gender='male'
        )
        session.add_all([president, member])

        # Create party and roles
        party = Party(name='Test Party')
        session.add(party)

        president_role = PASParliamentarianRole(
            parliamentarian=president,
            role='member',
            party=party,
            start=date(2025, 1, 1),
        )
        member_role = PASParliamentarianRole(
            parliamentarian=member,
            role='member',
            party=party,
            start=date(2025, 1, 1),
        )
        session.add_all([president_role, member_role])

        # Create commission memberships
        president_membership = PASCommissionMembership(
            commission=commission,
            parliamentarian=president,
            role='president',
            start=date(2025, 1, 1)
        )
        member_membership = PASCommissionMembership(
            commission=commission,
            parliamentarian=member,
            role='member',
            start=date(2025, 1, 1)
        )
        session.add_all([president_membership, member_membership])

        # Create attendances
        attendances = [
            Attendence(
                parliamentarian=president,
                date=date(2025, 2, 15),
                duration=60,  # 1 hour
                type='study',
                commission=commission
            ),
            Attendence(
                parliamentarian=member,
                date=date(2025, 2, 15),
                duration=60,  # 1 hour
                type='study',
                commission=commission
            ),
        ]
        session.add_all(attendances)

        # Create settlement run
        settlement_run = SettlementRun(
            name='Q1 2025 Test',
            start=date(2025, 1, 1),
            end=date(2025, 3, 31),
            active=True,
        )
        session.add(settlement_run)
        session.flush()
        transaction.commit()

    mock_request = Mock(spec=TownRequest)
    mock_request.session = session
    mock_request.translate = lambda x: x

    # Test the commission export function
    settlement_data = _get_commission_settlement_data(
        settlement_run, mock_request, commission
    )
    assert len(settlement_data) == 2
    settlement_data.sort(key=lambda x: x[1].last_name)

    # Verify member data (non-president)
    member_row = settlement_data[0]  # Member comes first alphabetically
    assert member_row[2] == 'File study'  # attendance type
    assert member_row[3] == Decimal('1.0')  # calculated value (1 hour)
    assert member_row[4] == Decimal('52')  # base rate (26 * 2 half-hours)
    assert member_row[5] == Decimal('63.40')

    # Verify president data
    president_row = settlement_data[1]  # President comes second alphabetically
    assert president_row[2] == 'File study'  # attendance type
    assert president_row[3] == Decimal('1.0')  # calculated value (1 hour)
    assert president_row[4] == Decimal('86')  # base rate (43 * 2 half-hours)
    assert president_row[5] == Decimal('104.85')

    totals = _settlement_totals(
        settlement_data,
        'party',
        'Total Test',
        session,
        settlement_run.start,
        settlement_run.end,
    )
    assert totals == [
        (
            'Test Party',
            Decimal('138.00'),
            Decimal('0'),
            Decimal('138.00'),
            Decimal('30.25'),
            Decimal('168.25'),
        ),
        (
            'Total Test',
            Decimal('138.00'),
            Decimal('0'),
            Decimal('138.00'),
            Decimal('30.25'),
            Decimal('168.25'),
        ),
    ]

    settlement_data.append(
        (
            settlement_run.end,
            president,
            LOHNART_ALLOWANCE_TEXT,
            Decimal('0'),
            Decimal('5000.00'),
            Decimal('6096.75'),
        )
    )
    totals_with_allowance = _settlement_totals(
        settlement_data,
        'party',
        'Total Test',
        session,
        settlement_run.start,
        settlement_run.end,
    )
    assert totals_with_allowance == [
        (
            'Test Party',
            Decimal('138.00'),
            Decimal('0'),
            Decimal('5138.00'),
            Decimal('1127.00'),
            Decimal('6265.00'),
        ),
        (
            'Total Test',
            Decimal('138.00'),
            Decimal('0'),
            Decimal('5138.00'),
            Decimal('1127.00'),
            Decimal('6265.00'),
        ),
    ]


def _settlement_pdf_html(
    settlement_run: SettlementRun,
    request: TownRequest,
    entity_type: Literal['all', 'commission', 'party'],
    entity: PASCommission | Party | None,
    monkeypatch: pytest.MonkeyPatch,
) -> str:
    html = Mock()
    html.write_pdf.return_value = b'%PDF'
    html_factory = Mock(return_value=html)
    monkeypatch.setattr(settlement_run_views, 'HTML', html_factory)
    monkeypatch.setattr(settlement_run_views, 'CSS', Mock())
    monkeypatch.setattr(settlement_run_views, 'FontConfiguration', Mock())

    generate_settlement_pdf(settlement_run, request, entity_type, entity)
    return html_factory.call_args.kwargs['string']


def test_settlement_pdf_formats_hours_as_decimal(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rate_set = RateSet(
        year=2024,
        cost_of_living_adjustment=Decimal('21.935'),
        plenary_none_member_halfday=Decimal('43'),
    )
    settlement_run = SettlementRun(
        name='Q1 2024',
        start=date(2024, 1, 1),
        end=date(2024, 3, 31),
        active=True,
    )
    parliamentarian = PASParliamentarian(
        first_name='Jane',
        last_name='Member',
        gender='female',
    )
    party = Party(name='Test Party')
    session.add_all(
        [
            rate_set,
            settlement_run,
            parliamentarian,
            party,
            PASParliamentarianRole(
                parliamentarian=parliamentarian,
                role='member',
                party=party,
                start=date(2024, 1, 1),
            ),
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 1, 15),
                duration=205,
                type='plenary',
            ),
        ]
    )
    session.flush()

    request = Mock(spec=TownRequest)
    request.session = session
    request.translate = lambda value: value

    entities: tuple[tuple[Literal['all', 'party'], Party | None], ...] = (
        ('all', None),
        ('party', party),
    )
    for entity_type, entity in entities:
        html = _settlement_pdf_html(
            settlement_run, request, entity_type, entity, monkeypatch
        )
        assert '3.416666' not in html
        assert '<td class="numeric">3.42</td>' in html


def test_settlement_pdf_lists_allowances_only_in_overview(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Amtliche Mission is only listed on the personal settlement and
    on the overview across all parties, never on a party or commission."""

    rate_set = RateSet(
        year=2024,
        cost_of_living_adjustment=Decimal('0'),
        study_normal_member_halfhour=Decimal('26'),
    )
    settlement_run = SettlementRun(
        name='Q1 2024',
        start=date(2024, 1, 1),
        end=date(2024, 3, 31),
        active=True,
    )
    commission = PASCommission(name='Test Commission', type='normal')
    left = Party(name='Left')
    right = Party(name='Right')
    presiding = PASParliamentarian(
        first_name='Anna',
        last_name='President',
        gender='female',
    )
    other = PASParliamentarian(
        first_name='Max',
        last_name='Member',
        gender='male',
    )
    session.add_all(
        [
            rate_set,
            settlement_run,
            commission,
            left,
            right,
            presiding,
            other,
            PASParliamentarianRole(
                parliamentarian=presiding,
                role='member',
                party=left,
                start=date(2024, 1, 1),
            ),
            PASParliamentarianRole(
                parliamentarian=other,
                role='member',
                party=right,
                start=date(2024, 1, 1),
            ),
            PASCommissionMembership(
                commission=commission,
                parliamentarian=other,
                role='member',
                start=date(2024, 1, 1),
            ),
            Attendence(
                parliamentarian=other,
                date=date(2024, 2, 15),
                duration=60,
                type='study',
                commission=commission,
            ),
        ]
    )
    session.flush()
    session.add(
        PresidentialAllowance(
            role='president',
            amount=5000,
            parliamentarian_id=presiding.id,
            settlement_run_id=settlement_run.id,
        )
    )
    session.flush()

    request = Mock(spec=TownRequest)
    request.session = session
    request.translate = lambda value: value

    commission_html = _settlement_pdf_html(
        settlement_run, request, 'commission', commission, monkeypatch
    )
    assert LOHNART_ALLOWANCE_TEXT not in commission_html
    assert '5,000.00' not in commission_html

    right_html = _settlement_pdf_html(
        settlement_run, request, 'party', right, monkeypatch
    )
    assert LOHNART_ALLOWANCE_TEXT not in right_html

    left_html = _settlement_pdf_html(
        settlement_run, request, 'party', left, monkeypatch
    )
    assert LOHNART_ALLOWANCE_TEXT not in left_html

    all_html = _settlement_pdf_html(
        settlement_run, request, 'all', None, monkeypatch
    )
    assert LOHNART_ALLOWANCE_TEXT in all_html


def test_plenary_uses_the_kantonsrat_president_rate(session: Session) -> None:
    """A plenary session has no commission, the president rate is decided
    by the Kantonsratspräsidium."""

    rate_set = RateSet(
        year=2024,
        cost_of_living_adjustment=Decimal('0'),
        plenary_none_president_halfday=Decimal('500'),
        plenary_none_member_halfday=Decimal('300'),
    )
    settlement_run = SettlementRun(
        name='Q1 2024',
        start=date(2024, 1, 1),
        end=date(2024, 3, 31),
        active=True,
    )
    president = PASParliamentarian(
        first_name='Anna',
        last_name='President',
        gender='female',
    )
    member = PASParliamentarian(
        first_name='Max',
        last_name='Member',
        gender='male',
    )
    party = Party(name='Test Party')
    president_role = PASParliamentarianRole(
        parliamentarian=president,
        role='president',
        party=party,
        start=date(2023, 12, 20),
    )
    president_role.meta = {'org_type': 'Kantonsrat'}
    member_role = PASParliamentarianRole(
        parliamentarian=member,
        role='member',
        party=party,
        start=date(2023, 12, 20),
    )
    member_role.meta = {'org_type': 'Kantonsrat'}
    session.add_all(
        [
            rate_set,
            settlement_run,
            party,
            president,
            member,
            president_role,
            member_role,
            Attendence(
                parliamentarian=president,
                date=date(2024, 1, 15),
                duration=205,
                type='plenary',
            ),
            Attendence(
                parliamentarian=member,
                date=date(2024, 1, 15),
                duration=205,
                type='plenary',
            ),
        ]
    )
    session.flush()

    request = Mock(spec=TownRequest)
    request.session = session
    request.translate = lambda value: value

    amounts = sorted(
        row[12] for row in generate_fibu_export_rows(settlement_run, request)
    )
    assert amounts == [Decimal('300'), Decimal('500')]
