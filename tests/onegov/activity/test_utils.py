from __future__ import annotations

from onegov.activity.iso20022 import get_esr
from onegov.activity.utils import merge_ranges
from onegov.activity.utils import extract_municipality


def test_merge_ranges() -> None:
    assert merge_ranges([(1, 2)]) == [(1, 2)]
    assert merge_ranges([(1, 2), (2, 3)]) == [(1, 3)]
    assert merge_ranges([(1, 2), (2, 3)]) == [(1, 3)]
    assert merge_ranges([(1, 2), (3, 4)]) == [(1, 2), (3, 4)]
    assert merge_ranges([(1, 2), (1, 2), (2, 3)]) == [(1, 3)]


def test_extract_municipality() -> None:
    assert extract_municipality("6004 Luzern") == (6004, 'Luzern')
    assert extract_municipality("9000 St. Gallen") == (9000, 'St. Gallen')
    assert extract_municipality("""
        Bahnhofstrasse 123
        1234 Test
    """) == (1234, "Test")
    assert extract_municipality("Bahnhofstrasse 123, 1234 Test")\
        == (1234, "Test")

    assert extract_municipality("""
        1234 Foo
        3456 Bar
    """) == (1234, "Foo")

    assert extract_municipality("0123 invalid plz") is None
    assert extract_municipality("4653 Obergösgen") == (4653, "Obergösgen")


def test_get_esr() -> None:
    # Test case 1: Valid 26 character ESR
    input_string = (
        'Gutschrift QRR Instant-Zahlung: 26 99029 05678 18860 27295 3705'
    )
    assert get_esr(input_string) == '269902905678188602729537054'

    # Test case 2: No valid ESR number
    input_string = "This string doesn't contain a valid ESR number"
    assert get_esr(input_string) is None

    # Test case 3: ESR number with any length
    input_string = 'Any length: 00 99029 05678 18860 27295 3705'
    assert get_esr(input_string) == '009902905678188602729537054'

    input_string = 'Any length: 0000 3705'
    assert get_esr(input_string) == '000000000000000000000037056'

    input_string = 'Any length: 37056'
    assert get_esr(input_string) == '000000000000000000000037056'

    # matches the first 27 digits
    input_string = '12345 23456 34567 45678 56789 67  890'
    assert get_esr(input_string) == '123452345634567456785678969'

    # test case 4: ESR of 27 character
    input_string = 'max length: 12 34567 89012 34567 89012 34567'
    assert get_esr(input_string) == '123456789012345678901234567'


def test_get_esr_with_different_prefix() -> None:
    input_string = 'Different prefix: 12 34567 89012 34567 89012 3456'
    assert get_esr(input_string) == '123456789012345678901234567'

    input_string = 'Different prefix: 12 34567 89012 34567 89012 34567'
    assert get_esr(input_string) == '123456789012345678901234567'


def test_get_esr_with_extra_spaces() -> None:
    # Test if string contains more whitespace
    input_string = 'Extra spaces:  26  99029  05678  18860  27295  3705 '
    assert get_esr(input_string) == '269902905678188602729537054'

    input_string = 'Extra newlines:  27  98029   05678  18861    27294  37065 '
    assert get_esr(input_string) == '279802905678188612729437068'

    input_string = ('Instant-Zahlung: 26 99029 05678                      '
                    '18860 27295 3705                  ')
    assert get_esr(input_string) == '269902905678188602729537054'


def test_get_esr_with_extra_newlines() -> None:
    """ Example with newline found in slip (number changed):
    'Gutschrift QRR Instant-Zahlung: 26 99029 05678
                    18860 27295 3705
                '
    """
    input_string = 'Extra newlines:  26 98029 05678\n18861 27294 3706\n'
    assert get_esr(input_string) == '269802905678188612729437061'

    input_string = 'Extra newlines:  27 98029 05678\n18861 27294 37068\n'
    assert get_esr(input_string) == '279802905678188612729437068'


def test_get_esr_no_spaces() -> None:
    input_string = 'Gutschrift QRR:  26980290567818861272943706'
    assert get_esr(input_string) == '269802905678188612729437061'

    input_string = 'Gutschrift QRR:  279802905678188612729437065'
    assert get_esr(input_string) == '279802905678188612729437068'
