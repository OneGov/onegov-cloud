from onegov.activity.iso20022 import get_esr
from onegov.activity.utils import merge_ranges
from onegov.activity.utils import extract_municipality


def test_merge_ranges():
    assert merge_ranges([[1, 2]]) == [(1, 2)]
    assert merge_ranges([[1, 2], [2, 3]]) == [(1, 3)]
    assert merge_ranges([[1, 2], [2, 3]]) == [(1, 3)]
    assert merge_ranges([[1, 2], [3, 4]]) == [(1, 2), (3, 4)]
    assert merge_ranges([[1, 2], [1, 2], [2, 3]]) == [(1, 3)]


def test_extract_municipality():
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


def test_get_esr():
    # Test case 1: Valid ESR number
    input_string = (
        'Gutschrift QRR Instant-Zahlung: 26 99029 05678 18860 27295 3705'
    )
    expected = '26990290567818860272953705'
    assert get_esr(input_string) == expected

    # Test case 2: No valid ESR number
    input_string = "This string doesn't contain a valid ESR number"
    expected = None
    assert get_esr(input_string) == expected

    # Test case 3: Partial match
    input_string = 'Partial match: 26 99029 05678 18860'
    expected = None
    assert get_esr(input_string) == expected


def test_get_esr_with_different_prefix():
    input_string = 'Different prefix: 12 34567 89012 34567 89012 3456'
    assert get_esr(input_string) == '12345678901234567890123456'


def test_get_esr_with_extra_spaces():
    # Test if string contains more whitesapce
    input_string = 'Extra spaces:  26  99029  05678  18860  27295  3705 '
    assert get_esr(input_string) == '26990290567818860272953705'
