from __future__ import annotations

import pytest

from datetime import date, datetime
from onegov.org.models.swiss_holidays import SwissHolidays


def test_empty_holidays() -> None:
    holidays = SwissHolidays()
    assert not holidays
    assert holidays.all(2021) == []
    assert list(holidays.official(2021)) == []
    assert date(2021, 1, 1) not in holidays


def test_add_canton_invalid() -> None:
    with pytest.raises(AssertionError):
        SwissHolidays().add_canton('XX')


def test_add_holiday_bounds() -> None:
    holidays = SwissHolidays()
    with pytest.raises(AssertionError):
        holidays.add_holiday(13, 1, 'invalid month')
    with pytest.raises(AssertionError):
        holidays.add_holiday(1, 32, 'invalid day')


def test_canton_holidays() -> None:
    holidays = SwissHolidays(cantons=['ZH'])
    assert holidays
    dates = [dt for dt, _ in holidays.all(2021)]
    assert date(2021, 1, 1) in dates   # Neujahrestag
    assert date(2021, 1, 2) in dates   # Berchtoldstag (ZH)
    assert date(2021, 1, 1) in holidays


def test_glarus_naefelser_fahrt() -> None:
    # GL has the special Näfelser Fahrt computation
    holidays = SwissHolidays(cantons=['GL'])
    dates = [dt for dt, _ in holidays.all(2021)]
    assert any(dt.month == 4 for dt in dates)


def test_other_holidays() -> None:
    holidays = SwissHolidays(other=[(8, 1, 'Nationalfeiertag')])
    assert date(2021, 8, 1) in holidays
    other = dict(holidays.other(2021))
    assert other[date(2021, 8, 1)] == {'Nationalfeiertag'}

    # a year-specific holiday only applies to its year
    specific = SwissHolidays(other=[(5, 1, 'Special', 2020)])
    assert date(2020, 5, 1) in specific
    assert date(2021, 5, 1) not in specific


def test_between() -> None:
    holidays = SwissHolidays(cantons=['ZH'])

    within = holidays.between(date(2021, 1, 1), date(2021, 1, 3))
    dates = [dt for dt, _ in within]
    assert date(2021, 1, 1) in dates
    assert all(date(2021, 1, 1) <= dt <= date(2021, 1, 3) for dt in dates)

    # a range spanning two years exercises the multi-year path
    cross = holidays.between(date(2020, 12, 24), date(2021, 1, 2))
    assert any(dt.year == 2020 for dt, _ in cross)
    assert any(dt.year == 2021 for dt, _ in cross)


def test_contains_rejects_datetime() -> None:
    holidays = SwissHolidays(cantons=['ZH'])
    with pytest.raises(TypeError):
        holidays.__contains__(datetime(2021, 1, 1))
