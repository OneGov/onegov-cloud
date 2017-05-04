import pytest

from onegov.activity.utils import append_checksum
from onegov.activity.utils import as_invoice_code
from onegov.activity.utils import decode_esr_reference
from onegov.activity.utils import encode_invoice_code
from onegov.activity.utils import format_esr_reference
from onegov.activity.utils import format_invoice_code
from onegov.activity.utils import generate_checksum
from onegov.activity.utils import is_valid_checksum
from onegov.activity.utils import merge_ranges


def test_merge_ranges():
    assert merge_ranges([[1, 2]]) == [(1, 2)]
    assert merge_ranges([[1, 2], [2, 3]]) == [(1, 3)]
    assert merge_ranges([[1, 2], [2, 3]]) == [(1, 3)]
    assert merge_ranges([[1, 2], [3, 4]]) == [(1, 2), (3, 4)]
    assert merge_ranges([[1, 2], [1, 2], [2, 3]]) == [(1, 3)]


def test_generate_checksum():
    assert generate_checksum("96111690000000660000000928") == 4
    assert generate_checksum("12000000000023447894321689") == 9


def test_append_checksum():
    assert append_checksum("96111690000000660000000928")\
        == "961116900000006600000009284"
    assert append_checksum("12000000000023447894321689")\
        == "120000000000234478943216899"


def test_is_valid_checksum():
    assert is_valid_checksum("961116900000006600000009284") is True
    assert is_valid_checksum("120000000000234478943216899") is True
    assert is_valid_checksum("961116900000006600000009285") is False
    assert is_valid_checksum("120000000000234478943216898") is False


def test_as_invoice_code():
    assert as_invoice_code('first', 'foo@example.org') == 'qeb3afd0e43'
    assert as_invoice_code('second', 'foo@example.org') == 'q9df17d0e43'
    assert as_invoice_code('first', 'bar@example.org') == 'q3717d883ed'


def test_format_invoice_code():
    assert format_invoice_code('qeb3afd0e43') == 'Q-EB3AF-D0E43'


def test_encode_invoice_code():
    assert encode_invoice_code('qca7df00e15') == '000127131108141601011502061'
    assert is_valid_checksum('000127131108141601011502061')


def test_decode_esr_reference():
    assert decode_esr_reference('000127131108141601011502061') == 'qca7df00e15'
    assert decode_esr_reference('127131108141601011502061') == 'qca7df00e15'
    assert decode_esr_reference('1 2713 1108141601011502061') == 'qca7df00e15'

    def assert_raises_error(code, message):
        with pytest.raises(RuntimeError) as e:
            decode_esr_reference(code)
        assert e.value.args[0] == message

    assert_raises_error(
        '000227131108141601011502069',
        'Unknown ESR reference version: 2')

    assert_raises_error(
        '000227131108141601011502069123123',
        'ESR reference is too long')

    assert_raises_error(
        '127131108141601011502062',
        'ESR reference has an invalid checksum')

    assert_raises_error(
        '11',
        'ESR reference is too short'
    )

    assert_raises_error(
        '1271311081416010115020610',
        'ESR reference has an uneven number of digits'
    )


def test_format_esr_reference():
    assert format_esr_reference('000127131108141601011502061')\
        == '1271 31108 14160 10115 02061'

    assert format_esr_reference('127131108141601011502061')\
        == '1271 31108 14160 10115 02061'
