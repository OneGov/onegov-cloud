from __future__ import annotations

from datetime import datetime
from onegov.activity.models.occasion_date import DAYS, OccasionDate
from sedate import replace_timezone


def test_days_has() -> None:
    assert DAYS.has(0b11, DAYS.half) is True
    assert DAYS.has(0b10, DAYS.half) is False
    assert DAYS.has(0, DAYS.half) is False


def test_days_compute_half() -> None:
    start = datetime(2021, 6, 1, 10)
    assert DAYS.compute(start, start, 4 * 3600) == DAYS.half


def test_days_compute_full_same_day() -> None:
    start = datetime(2021, 6, 1, 10)
    end = datetime(2021, 6, 1, 20)
    assert DAYS.compute(start, end, 10 * 3600) == DAYS.full


def test_days_compute_many_cross_day_late_end() -> None:
    start = datetime(2021, 6, 1, 20)
    end = datetime(2021, 6, 2, 10)  # ends after 06:00 next day
    assert DAYS.compute(start, end, 14 * 3600) == DAYS.many


def test_days_compute_full_cross_day_early_end() -> None:
    start = datetime(2021, 6, 1, 20)
    end = datetime(2021, 6, 2, 4)  # ends before 06:00 next day
    assert DAYS.compute(start, end, 8 * 3600) == DAYS.full


def test_days_compute_many_long() -> None:
    start = datetime(2021, 6, 1, 10)
    end = datetime(2021, 6, 3, 10)
    assert DAYS.compute(start, end, 48 * 3600) == DAYS.many


def _occasion_date(start: datetime, end: datetime) -> OccasionDate:
    return OccasionDate(
        id=1,
        start=replace_timezone(start, 'UTC'),
        end=replace_timezone(end, 'UTC'),
        timezone='Europe/Zurich',
    )


def test_occasion_date_properties() -> None:
    od = _occasion_date(
        datetime(2021, 6, 1, 8), datetime(2021, 6, 1, 12))
    assert od.duration_in_seconds == 4 * 3600
    assert od.duration == DAYS.half
    assert hash(od) == hash(1)
    # 2021-06-01 is a Tuesday
    assert od.weekdays == [1]
    assert len(list(od.active_days)) == 1


def test_occasion_date_overlaps() -> None:
    a = _occasion_date(datetime(2021, 6, 1, 8), datetime(2021, 6, 1, 12))
    b = _occasion_date(datetime(2021, 6, 1, 10), datetime(2021, 6, 1, 14))
    c = _occasion_date(datetime(2021, 6, 2, 8), datetime(2021, 6, 2, 12))
    assert a.overlaps(b) is True
    assert a.overlaps(c) is False
