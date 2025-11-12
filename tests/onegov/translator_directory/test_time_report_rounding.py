"""
Tests for time report duration rounding logic.

This is critical as actual money is involved in translator compensation.
The rounding logic ensures translators are billed in 30-minute increments,
always rounding UP.
"""
from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

import pytest

from onegov.core.utils import Bunch
from onegov.translator_directory.forms.time_report import (
    TranslatorTimeReportForm
)
from tests.onegov.translator_directory.shared import create_translator


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestApp


def test_rounding_to_nearest_half_hour(translator_app: TestApp) -> None:
    """Test that duration is rounded up to nearest 0.5 hour."""
    session = translator_app.session()
    translator = create_translator(translator_app)

    request: object = Bunch(
        app=translator_app,
        session=session,
        locale='de_CH',
        translate=lambda x: str(x),
    )

    form = TranslatorTimeReportForm()
    form.request = request  # type: ignore[assignment]
    form.on_request()

    # Test exact half hour (no rounding needed)
    form.start_date.data = datetime(2025, 1, 1).date()
    form.start_time.data = time(9, 0)
    form.end_date.data = datetime(2025, 1, 1).date()
    form.end_time.data = time(9, 30)
    assert form.get_duration_hours() == Decimal('0.5')

    # Test exact hour (no rounding needed)
    form.end_time.data = time(10, 0)
    assert form.get_duration_hours() == Decimal('1.0')

    # Test 1 minute over - should round up to 0.5
    form.end_time.data = time(9, 1)
    assert form.get_duration_hours() == Decimal('0.5')

    # Test 10 minutes - should round up to 0.5
    form.end_time.data = time(9, 10)
    assert form.get_duration_hours() == Decimal('0.5')

    # Test 31 minutes - should round up to 1.0
    form.end_time.data = time(9, 31)
    assert form.get_duration_hours() == Decimal('1.0')

    # Test 1 hour 1 minute - should round up to 1.5
    form.end_time.data = time(10, 1)
    assert form.get_duration_hours() == Decimal('1.5')

    # Test 1 hour 30 minutes - exact, no rounding
    form.end_time.data = time(10, 30)
    assert form.get_duration_hours() == Decimal('1.5')

    # Test 1 hour 31 minutes - should round up to 2.0
    form.end_time.data = time(10, 31)
    assert form.get_duration_hours() == Decimal('2.0')

    # Test 2 hours 45 minutes - should round up to 3.0
    form.end_time.data = time(11, 45)
    assert form.get_duration_hours() == Decimal('3.0')


def test_edge_cases_rounding(translator_app: TestApp) -> None:
    """Test edge cases for rounding logic."""
    session = translator_app.session()
    translator = create_translator(translator_app)

    request: object = Bunch(
        app=translator_app,
        session=session,
        locale='de_CH',
        translate=lambda x: str(x),
    )

    form = TranslatorTimeReportForm()
    form.request = request  # type: ignore[assignment]
    form.on_request()

    # Minimum billable unit: 1 minute -> rounds to 0.5 hour
    form.start_date.data = datetime(2025, 1, 1).date()
    form.start_time.data = time(9, 0)
    form.end_date.data = datetime(2025, 1, 1).date()
    form.end_time.data = time(9, 1)
    assert form.get_duration_hours() == Decimal('0.5')

    # 5 seconds over 30 minutes -> should round to 1.0
    # 30 min 5 sec = 1805 seconds = 0.50138... hours
    form.end_time.data = time(9, 30, 5)
    duration = form.get_duration_hours()
    # This should round up to 1.0 hour
    assert duration == Decimal('1.0')

    # Exactly 29 minutes 59 seconds -> should round to 0.5
    form.end_time.data = time(9, 29, 59)
    assert form.get_duration_hours() == Decimal('0.5')


def test_compensation_calculation_with_rounding(
    translator_app: TestApp
) -> None:
    """Test that rounding affects compensation correctly."""
    session = translator_app.session()
    translator = create_translator(translator_app, admission='certified')

    request: object = Bunch(
        app=translator_app,
        session=session,
        locale='de_CH',
        translate=lambda x: str(x),
    )

    form = TranslatorTimeReportForm()
    form.request = request  # type: ignore[assignment]
    form.on_request()

    # Set up 1 hour 10 minutes of work
    # Should round to 1.5 hours
    form.start_date.data = datetime(2025, 1, 1).date()
    form.start_time.data = time(9, 0)
    form.end_date.data = datetime(2025, 1, 1).date()
    form.end_time.data = time(10, 10)
    form.assignment_type.data = 'on-site'

    # Certified translator rate is CHF 90/hour
    hourly_rate = form.get_hourly_rate(translator)
    assert hourly_rate == Decimal('90.00')

    # Duration should be rounded to 1.5 hours
    duration = form.get_duration_hours()
    assert duration == Decimal('1.5')

    # Base pay should be 90 * 1.5 = 135
    expected_base = hourly_rate * duration
    assert expected_base == Decimal('135.00')


def test_uncertified_translator_rate(translator_app: TestApp) -> None:
    """Test compensation calculation for uncertified translators."""
    session = translator_app.session()
    translator = create_translator(translator_app, admission='uncertified')

    request: object = Bunch(
        app=translator_app,
        session=session,
        locale='de_CH',
        translate=lambda x: str(x),
    )

    form = TranslatorTimeReportForm()
    form.request = request  # type: ignore[assignment]
    form.on_request()

    # Uncertified translator rate is CHF 75/hour
    hourly_rate = form.get_hourly_rate(translator)
    assert hourly_rate == Decimal('75.00')

    # 40 minutes should round to 1.0 hour
    form.start_date.data = datetime(2025, 1, 1).date()
    form.start_time.data = time(9, 0)
    form.end_date.data = datetime(2025, 1, 1).date()
    form.end_time.data = time(9, 40)
    form.assignment_type.data = 'on-site'

    duration = form.get_duration_hours()
    assert duration == Decimal('1.0')

    # Base pay should be 75 * 1.0 = 75
    expected_base = hourly_rate * duration
    assert expected_base == Decimal('75.00')


def test_multi_day_assignment(translator_app: TestApp) -> None:
    """Test rounding for assignments spanning multiple days."""
    session = translator_app.session()
    translator = create_translator(translator_app)

    request: object = Bunch(
        app=translator_app,
        session=session,
        locale='de_CH',
        translate=lambda x: str(x),
    )

    form = TranslatorTimeReportForm()
    form.request = request  # type: ignore[assignment]
    form.on_request()

    # Start at 11:00 PM, end at 2:00 AM next day = 3 hours
    form.start_date.data = datetime(2025, 1, 1).date()
    form.start_time.data = time(23, 0)
    form.end_date.data = datetime(2025, 1, 2).date()
    form.end_time.data = time(2, 0)
    assert form.get_duration_hours() == Decimal('3.0')

    # Start at 11:00 PM, end at 2:15 AM next day = 3h 15min -> 3.5h
    form.end_time.data = time(2, 15)
    assert form.get_duration_hours() == Decimal('3.5')

    # Start at 11:00 PM, end at 2:20 AM next day = 3h 20min -> 3.5h
    form.end_time.data = time(2, 20)
    assert form.get_duration_hours() == Decimal('3.5')

    # Start at 11:00 PM, end at 2:31 AM next day = 3h 31min -> 4.0h
    form.end_time.data = time(2, 31)
    assert form.get_duration_hours() == Decimal('4.0')


@pytest.mark.parametrize(
    'minutes,expected_rounded_hours',
    [
        (1, 0.5),  # 1 minute -> 0.5 hours
        (15, 0.5),  # 15 minutes -> 0.5 hours
        (29, 0.5),  # 29 minutes -> 0.5 hours
        (30, 0.5),  # 30 minutes -> 0.5 hours (exact)
        (31, 1.0),  # 31 minutes -> 1.0 hour
        (45, 1.0),  # 45 minutes -> 1.0 hour
        (60, 1.0),  # 60 minutes -> 1.0 hour (exact)
        (61, 1.5),  # 61 minutes -> 1.5 hours
        (90, 1.5),  # 90 minutes -> 1.5 hours (exact)
        (91, 2.0),  # 91 minutes -> 2.0 hours
        (105, 2.0),  # 105 minutes (1h 45m) -> 2.0 hours
        (120, 2.0),  # 120 minutes -> 2.0 hours (exact)
        (121, 2.5),  # 121 minutes -> 2.5 hours
        (150, 2.5),  # 150 minutes -> 2.5 hours (exact)
        (180, 3.0),  # 180 minutes -> 3.0 hours (exact)
        (181, 3.5),  # 181 minutes -> 3.5 hours
        (240, 4.0),  # 240 minutes -> 4.0 hours (exact)
        (480, 8.0),  # 480 minutes (8 hours) -> 8.0 hours
        (481, 8.5),  # 481 minutes -> 8.5 hours
    ],
)
def test_parametric_rounding(
    translator_app: TestApp,
    minutes: int,
    expected_rounded_hours: float
) -> None:
    """Parametric test for various minute values and their rounding."""
    session = translator_app.session()
    translator = create_translator(translator_app)

    request: object = Bunch(
        app=translator_app,
        session=session,
        locale='de_CH',
        translate=lambda x: str(x),
    )

    form = TranslatorTimeReportForm()
    form.request = request  # type: ignore[assignment]
    form.on_request()

    # Calculate hours and minutes
    hours = minutes // 60
    remaining_minutes = minutes % 60

    form.start_date.data = datetime(2025, 1, 1).date()
    form.start_time.data = time(9, 0)
    form.end_date.data = datetime(2025, 1, 1).date()
    form.end_time.data = time(9 + hours, remaining_minutes)

    result = form.get_duration_hours()
    expected = Decimal(str(expected_rounded_hours))
    assert result == expected, (
        f'{minutes} minutes should round to {expected_rounded_hours} hours, '
        f'but got {result}'
    )
