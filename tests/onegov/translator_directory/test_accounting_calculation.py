from __future__ import annotations


from datetime import date, datetime, timezone
from decimal import Decimal
from onegov.translator_directory.collections.translator import (
    TranslatorCollection,
)
from onegov.translator_directory.models.time_report import (
    TranslatorTimeReport,
)
from onegov.translator_directory.views.time_report import (
    calculate_accounting_values,
)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import Client


def assert_accounting_calculation_matches(
    report: TranslatorTimeReport, tolerance: Decimal = Decimal('0.01')
) -> None:
    """Verify accounting calculation matches model calculation.

    The accounting system multiplies duration_hours × effective_rate.
    This must equal the adjusted_subtotal from the model within tolerance.
    """
    breakdown = report.calculate_compensation_breakdown()
    duration, rate, recalculated = calculate_accounting_values(report)

    expected = breakdown['adjusted_subtotal']
    diff = abs(recalculated - expected)

    assert diff <= tolerance, (
        f'Accounting calculation mismatch:\n'
        f'  Duration: {duration}h\n'
        f'  Effective rate: CHF {rate}/h\n'
        f'  Recalculated (duration × rate): CHF {recalculated}\n'
        f'  Expected (adjusted_subtotal): CHF {expected}\n'
        f'  Difference: CHF {diff} (tolerance: CHF {tolerance})\n'
        f'  Breakdown: {breakdown}'
    )


def test_simple_work_no_surcharges(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='polizei',
        duration=90,
        case_number='CASE-001',
        assignment_date=date(2025, 1, 15),
        hourly_rate=Decimal('90.0'),
        travel_compensation=Decimal('0'),
        total_compensation=Decimal('0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    assert_accounting_calculation_matches(report)


def test_night_work_surcharge(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    start = datetime(2025, 1, 15, 22, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 16, 4, 0, tzinfo=timezone.utc)

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='polizei',
        duration=360,
        night_minutes=360,
        case_number='CASE-002',
        assignment_date=date(2025, 1, 15),
        start=start,
        end=end,
        hourly_rate=Decimal('90.0'),
        travel_compensation=Decimal('0'),
        total_compensation=Decimal('0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    assert_accounting_calculation_matches(report)


def test_mixed_day_and_night_work(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    start = datetime(2025, 1, 15, 18, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 16, 2, 0, tzinfo=timezone.utc)

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='polizei',
        duration=480,
        night_minutes=240,
        case_number='CASE-003',
        assignment_date=date(2025, 1, 15),
        start=start,
        end=end,
        hourly_rate=Decimal('90.0'),
        travel_compensation=Decimal('0'),
        total_compensation=Decimal('0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    assert_accounting_calculation_matches(report)


def test_weekend_surcharge(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='polizei',
        duration=240,
        weekend_holiday_minutes=240,
        case_number='CASE-004',
        assignment_date=date(2025, 1, 18),
        hourly_rate=Decimal('90.0'),
        surcharge_types=['weekend_holiday'],
        travel_compensation=Decimal('0'),
        total_compensation=Decimal('0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    assert_accounting_calculation_matches(report)


def test_urgent_surcharge(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='polizei',
        duration=120,
        case_number='CASE-005',
        assignment_date=date(2025, 1, 15),
        hourly_rate=Decimal('90.0'),
        surcharge_types=['urgent'],
        travel_compensation=Decimal('0'),
        total_compensation=Decimal('0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    assert_accounting_calculation_matches(report)


def test_break_time_deduction(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='polizei',
        duration=420,
        break_time=30,
        case_number='CASE-006',
        assignment_date=date(2025, 1, 15),
        hourly_rate=Decimal('90.0'),
        travel_compensation=Decimal('0'),
        total_compensation=Decimal('0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    assert_accounting_calculation_matches(report)


def test_all_surcharges_combined(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    # 18.1 to 19.1.2025 (Saturday to Sunday, night work)
    # 3 hour day work (weekend work)
    # 2 hour night work
    start = datetime(2025, 1, 18, 17, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 18, 22, 0, 0, tzinfo=timezone.utc)

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='on-site',
        finanzstelle='polizei',
        duration=300,
        break_time=60,
        case_number='CASE-007',
        assignment_date=date(2025, 1, 18),
        start=start,
        end=end,
        hourly_rate=Decimal('90.0'),
        surcharge_types=['weekend_holiday', 'urgent'],
        total_compensation=Decimal('0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    assert_accounting_calculation_matches(report)


def test_uncertified_translator_lower_rate(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='uncertified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='polizei',
        duration=120,
        case_number='CASE-008',
        assignment_date=date(2025, 1, 15),
        hourly_rate=Decimal('75.0'),
        travel_compensation=Decimal('0'),
        total_compensation=Decimal('0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    assert_accounting_calculation_matches(report)


def test_fractional_hours_rounding(client: Client) -> None:
    session = client.app.session()
    translators = TranslatorCollection(client.app)

    translator = translators.add(
        first_name='Test',
        last_name='Translator',
        admission='certified',
        email='test@example.org',
        pers_id='12345',
    )
    session.flush()

    report = TranslatorTimeReport(
        translator_id=translator.id,
        assignment_type='consecutive',
        finanzstelle='polizei',
        duration=77,
        night_minutes=23,
        case_number='CASE-009',
        assignment_date=date(2025, 1, 15),
        hourly_rate=Decimal('90.0'),
        travel_compensation=Decimal('0'),
        total_compensation=Decimal('0'),
        status='confirmed',
    )
    session.add(report)
    session.flush()

    assert_accounting_calculation_matches(report)
