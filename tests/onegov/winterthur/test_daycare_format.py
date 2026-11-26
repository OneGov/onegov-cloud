from __future__ import annotations

from decimal import Decimal
from onegov.winterthur.daycare import (
    format_1_cent,
    format_5_cents,
    format_precise,
    round_to,
)


def test_round_to() -> None:
    assert round_to(Decimal('1.23'), '0.05') == Decimal('1.25')
    assert round_to(Decimal('1.22'), '0.05') == Decimal('1.20')
    # negative values use the negative correction
    assert round_to(Decimal('-1.23'), '0.05') == Decimal('-1.25')


def test_format_precise() -> None:
    # falsy amounts render as 0.00
    assert format_precise(None) == '0.00'
    assert format_precise(Decimal('0')) == '0.00'

    formatted = format_precise(Decimal('1234.5'))
    assert formatted.endswith('.50')
    assert '234' in formatted


def test_format_1_cent() -> None:
    assert format_1_cent(Decimal('1.234')) == '1.23'


def test_format_5_cents() -> None:
    assert format_5_cents(Decimal('1.23')) == '1.25'
