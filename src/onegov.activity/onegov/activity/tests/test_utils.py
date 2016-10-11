from onegov.activity.utils import merge_ranges


def test_merge_ranges():
    assert merge_ranges([[1, 2]]) == [(1, 2)]
    assert merge_ranges([[1, 2], [2, 3]]) == [(1, 3)]
    assert merge_ranges([[1, 2], [2, 3]]) == [(1, 3)]
    assert merge_ranges([[1, 2], [3, 4]]) == [(1, 2), (3, 4)]
    assert merge_ranges([[1, 2], [1, 2], [2, 3]]) == [(1, 3)]
