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
