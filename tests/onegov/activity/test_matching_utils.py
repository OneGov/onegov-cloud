from __future__ import annotations

import pytest

from decimal import Decimal
from onegov.activity.matching.utils import (
    HashableID,
    LoopBudget,
    booking_order,
    overlaps,
)
from types import SimpleNamespace
from uuid import uuid4


from typing import Any


def _obj(**kwargs: Any) -> Any:
    return SimpleNamespace(**kwargs)


def test_loop_budget() -> None:
    budget = LoopBudget(max_ticks=2)
    assert budget.limit_reached() is False
    assert budget.limit_reached() is False
    assert budget.limit_reached() is True

    with pytest.raises(RuntimeError):
        LoopBudget(max_ticks=0).limit_reached(as_exception=True)


def test_hashable_id() -> None:
    class Item(HashableID):
        def __init__(self, id: int) -> None:
            self.id = id

    assert Item(1) == Item(1)
    assert Item(1) != Item(2)
    assert Item(1) != object()
    assert hash(Item(1)) == hash(Item(1))


def test_booking_order() -> None:
    uid = uuid4()
    booking = _obj(score=Decimal(5), priority=2, id=uid)
    assert booking_order(booking) == (Decimal(-5), -2, uid)


def test_overlaps_same_id() -> None:
    assert overlaps(_obj(id=1), _obj(id=1)) is True


def test_overlaps_excluded() -> None:
    booking = _obj(
        id=1, occasion=_obj(exclude_from_overlap_check=True))
    other = _obj(id=2, exclude_from_overlap_check=False)
    assert overlaps(booking, other) is False
