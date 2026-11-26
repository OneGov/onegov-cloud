from __future__ import annotations

import pytest

from datetime import date
from decimal import Decimal
from onegov.pas.utils import (
    _is_kantonsrat_role,
    format_swiss_number,
    is_active_kantonsrat_member,
    is_kantonsrat_president,
    is_president_for_attendance,
)
from types import SimpleNamespace


from typing import Any


def _role(**kwargs: Any) -> Any:
    kwargs.setdefault('meta', {'org_type': 'Kantonsrat'})
    kwargs.setdefault('start', None)
    kwargs.setdefault('end', None)
    kwargs.setdefault('role', 'member')
    return SimpleNamespace(**kwargs)


def _obj(**kwargs: Any) -> Any:
    return SimpleNamespace(**kwargs)


def test_format_swiss_number() -> None:
    assert format_swiss_number(5) == '5.00'
    formatted = format_swiss_number(Decimal('1234.5'))
    assert formatted.endswith('.50')
    assert '234' in formatted

    with pytest.raises(TypeError):
        format_swiss_number('not a number')  # type: ignore[arg-type]


def test_is_kantonsrat_role() -> None:
    assert _is_kantonsrat_role(_role(meta={'org_type': 'Kantonsrat'})) is True
    assert _is_kantonsrat_role(_role(meta={'org_type': 'Other'})) is False
    assert _is_kantonsrat_role(_role(meta={})) is False


def test_is_active_kantonsrat_member() -> None:
    ref = date(2021, 6, 1)

    active = _obj(roles=[_role(start=date(2020, 1, 1), end=None)])
    assert is_active_kantonsrat_member(active, ref) is True

    expired = _obj(
        roles=[_role(start=date(2019, 1, 1), end=date(2020, 1, 1))])
    assert is_active_kantonsrat_member(expired, ref) is False

    # a non-kantonsrat role does not count
    other = _obj(roles=[_role(meta={'org_type': 'Other'})])
    assert is_active_kantonsrat_member(other, ref) is False


def test_is_kantonsrat_president() -> None:
    on_date = date(2021, 6, 1)

    president = _obj(roles=[_role(
        role='president', start=date(2020, 1, 1), end=None)])
    assert is_kantonsrat_president(president, on_date) is True

    member = _obj(roles=[_role(role='member')])
    assert is_kantonsrat_president(member, on_date) is False


def test_is_president_for_attendance() -> None:
    president = _obj(
        roles=[_role(role='president')],
        has_commission_presidency=lambda on_date, commission_id: True,
    )

    # a plenary session defers to the kantonsrat president
    plenary = _obj(type='plenary', date=date(2021, 6, 1))
    assert is_president_for_attendance(president, plenary) is True

    # a commission session without a commission id is never president
    no_commission = _obj(
        type='commission', commission_id=None, date=date(2021, 6, 1))
    assert is_president_for_attendance(president, no_commission) is False

    # a commission session defers to has_commission_presidency
    commission = _obj(
        type='commission', commission_id='c1', date=date(2021, 6, 1))
    assert is_president_for_attendance(president, commission) is True
