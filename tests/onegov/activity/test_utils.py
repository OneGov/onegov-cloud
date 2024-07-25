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
    expected = '269902905678188602729537054'  # including checksum
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
    assert (get_esr(input_string)
            == '123456789012345678901234567')  # including checksum

    input_string = 'Different prefix: 12 34567 89012 34567 89012 34567'
    assert (get_esr(input_string)
            == '123456789012345678901234567')


def test_get_esr_with_extra_spaces():
    # Test if string contains more whitespace
    input_string = 'Extra spaces:  26  99029  05678  18860  27295  3705 '
    assert (get_esr(input_string)
            == '269902905678188602729537054')  # including checksum

    input_string = 'Extra newlines:  27  98029   05678  18861    27294  37065 '
    assert (get_esr(input_string)
            == '279802905678188612729437065')

    input_string = ('Instant-Zahlung: 26 99029 05678                      '
                    '18860 27295 3705                  ')
    assert (get_esr(input_string)
            == '269902905678188602729537054')  # including checksum


def test_get_esr_with_extra_newlines():
    """ Example with newline found in slip (number changed):
    'Gutschrift QRR Instant-Zahlung: 26 99029 05678
                    18860 27295 3705
                '
    """
    input_string = 'Extra newlines:  26 98029 05678\n18861 27294 3706\n'
    assert (get_esr(input_string)
            == '269802905678188612729437061')  # including checksum

    input_string = 'Extra newlines:  27 98029 05678\n18861 27294 37065\n'
    assert get_esr(input_string) == '279802905678188612729437065'


def test_get_esr_no_spaces():
    input_string = 'Gutschrift QRR:  26980290567818861272943706'
    assert (get_esr(input_string)
            == '269802905678188612729437061')  # including checksum

    input_string = 'Gutschrift QRR:  279802905678188612729437065'
    assert get_esr(input_string) == '279802905678188612729437065'
