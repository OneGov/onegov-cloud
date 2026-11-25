from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from onegov.org.pricing_schemes.stadtschulen_zug import StadtschulenZug
from types import SimpleNamespace
from uuid import uuid4


from typing import Any

# [base_rates, hourly_rates, daily_maxes] per category (A, B, C)
TABLE = [
    [Decimal(10), Decimal(20), Decimal(30)],
    [Decimal(5), Decimal(5), Decimal(5)],
    [Decimal(100), Decimal(100), Decimal(100)],
]


def _reservation(start: datetime, end: datetime, data: Any = None) -> Any:
    payload = {'stadtschulen_zug_price_table': TABLE}
    if data is not None:
        payload = data
    return SimpleNamespace(data=payload, start=start, end=end, id=uuid4())


def _price(reservation: Any, submission: Any, resource: Any = None) -> Any:
    res: Any = resource
    if res is None:
        res = SimpleNamespace(content={})
    return StadtschulenZug.reservation_unit_price(reservation, res, submission)


def test_no_submission_data() -> None:
    start = datetime(2021, 1, 4, 10)
    assert _price(
        _reservation(start, start + timedelta(hours=1)), None) is None


def test_base_rate_under_four_hours() -> None:
    start = datetime(2021, 1, 4, 10)
    end = start + timedelta(hours=2)
    # category A, no extra hours -> base rate
    assert _price(_reservation(start, end), {'kategorie': 'A'}) == Decimal(10)


def test_extra_hours() -> None:
    start = datetime(2021, 1, 4, 10)
    end = start + timedelta(hours=6)
    # category A: base 10 + 2 extra hours * 5
    price = _price(_reservation(start, end), {'kategorie': 'A'})
    assert round(price, 2) == Decimal('20.00')


def test_daily_cap() -> None:
    start = datetime(2021, 1, 4, 10)
    end = start + timedelta(hours=100)
    # fee would exceed the daily max and is capped at 100
    assert _price(_reservation(start, end), {'kategorie': 'A'}) == Decimal(100)


def test_missing_category_falls_back_to_c() -> None:
    start = datetime(2021, 1, 4, 10)
    end = start + timedelta(hours=2)
    # no category -> fallback to C -> base rate 30
    assert _price(_reservation(start, end), {}) == Decimal(30)


def test_table_from_resource() -> None:
    start = datetime(2021, 1, 4, 10)
    end = start + timedelta(hours=2)
    reservation = SimpleNamespace(
        data={}, start=start, end=end, id=uuid4())
    resource = SimpleNamespace(
        content={'stadtschulen_zug_price_table': TABLE})
    assert _price(reservation, {'kategorie': 'B'}, resource) == Decimal(20)
