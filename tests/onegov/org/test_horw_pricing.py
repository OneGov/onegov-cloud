from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from onegov.org.pricing_schemes.horw import HorwHorwerhalle
from types import SimpleNamespace
from uuid import uuid4


from typing import Any

# rows indexed by (0/2 non-profit/profit) + (0/1 without/with wirtschaft):
# each row is (two_hours, half_day, full_day)
TABLE = [
    [Decimal(10), Decimal(20), Decimal(30)],  # non-profit, no wirtschaft
    [Decimal(11), Decimal(21), Decimal(31)],  # non-profit, wirtschaft
    [Decimal(12), Decimal(22), Decimal(32)],  # profit, no wirtschaft
    [Decimal(13), Decimal(23), Decimal(33)],  # profit, wirtschaft
]


def _reservation(start: datetime, end: datetime, data: Any = None) -> Any:
    payload = {'horw_horwerhalle_price_table': TABLE}
    if data:
        payload.update(data)
    return SimpleNamespace(data=payload, start=start, end=end, id=uuid4())


def _resource(content: Any = None) -> Any:
    return SimpleNamespace(content=content or {})


def _price(reservation: Any, submission: Any, resource: Any = None) -> Any:
    return HorwHorwerhalle.reservation_unit_price(
        reservation, resource or _resource(), submission)


def test_no_submission_data() -> None:
    start = datetime(2021, 1, 4, 10)
    assert _price(
        _reservation(start, start + timedelta(hours=1)), None) is None


def test_profit_two_hours() -> None:
    start = datetime(2021, 1, 4, 10)  # Monday
    end = start + timedelta(hours=1)
    assert _price(_reservation(start, end), {}) == Decimal(12)


def test_profit_with_wirtschaft() -> None:
    start = datetime(2021, 1, 4, 10)
    end = start + timedelta(hours=1)
    submission = {'mit_wirtschaft': 'Ja'}
    assert _price(_reservation(start, end), submission) == Decimal(13)


def test_nonprofit_weekday_is_free() -> None:
    start = datetime(2021, 1, 4, 10)  # Monday (weekday < 5)
    end = start + timedelta(hours=1)
    submission = {'horwer_non_profit_organisation': 'Ja'}
    assert _price(_reservation(start, end), submission) is None


def test_full_day_on_weekend() -> None:
    start = datetime(2021, 1, 9, 10)  # Saturday
    end = start + timedelta(hours=6)
    assert _price(_reservation(start, end), {}) == Decimal(32)


def test_half_day_table_from_resource() -> None:
    start = datetime(2021, 1, 9, 10)  # Saturday
    end = start + timedelta(hours=3)
    reservation = SimpleNamespace(data={}, start=start, end=end, id=uuid4())
    resource = _resource({'horw_horwerhalle_price_table': TABLE})
    assert _price(reservation, {}, resource) == Decimal(22)
