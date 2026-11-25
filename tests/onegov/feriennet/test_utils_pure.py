from __future__ import annotations

from onegov.feriennet.utils import (
    decode_name,
    encode_name,
    format_donation_amounts,
    parse_donation_amounts,
    tos_accepted_periods,
)

NBSP = ' '


def test_encode_name() -> None:
    assert encode_name('Anna', 'Alpha') == f'Anna{NBSP}Alpha'
    # an embedded non-breaking space is normalised to a regular space
    assert encode_name(f'Anna{NBSP}Maria', 'Alpha') == f'Anna Maria{NBSP}Alpha'


def test_decode_name() -> None:
    assert decode_name(f'Anna{NBSP}Alpha') == ('Anna', 'Alpha')
    assert decode_name('Anna') == ('Anna', None)
    assert decode_name(None) == (None, None)
    assert decode_name('') == (None, None)


def test_roundtrip_name() -> None:
    assert decode_name(encode_name('Anna', 'Alpha')) == ('Anna', 'Alpha')


def test_tos_accepted_periods() -> None:
    assert tos_accepted_periods({'tos_accepted': ['a', 'b']}) == ['a', 'b']
    # legacy True values count as not accepted
    assert tos_accepted_periods({'tos_accepted': True}) == []
    assert tos_accepted_periods(None) == []
    # non-string entries are filtered out
    assert tos_accepted_periods({'tos_accepted': ['a', 1, 'b']}) == ['a', 'b']


def test_parse_donation_amounts() -> None:
    parsed = parse_donation_amounts('10\n25.03\nnot a number\n')
    # amounts are rounded to the nearest 0.05, invalid lines are skipped
    assert parsed == (10.0, 25.05)


def test_format_donation_amounts() -> None:
    assert format_donation_amounts([10, 25.5]) == '10\n25.50'
