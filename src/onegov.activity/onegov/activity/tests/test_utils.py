from onegov.activity.utils import merge_ranges
from onegov.activity.utils import generate_checksum
from onegov.activity.utils import append_checksum
from onegov.activity.utils import is_valid_checksum


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
