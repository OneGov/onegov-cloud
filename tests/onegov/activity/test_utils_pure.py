from __future__ import annotations

from datetime import date, datetime
from onegov.activity.utils import (
    dates_overlap,
    date_range_decode,
    date_range_encode,
    extract_municipality,
    extract_thumbnail,
    is_internal_image,
    is_valid_group_code,
    num_range_decode,
    num_range_encode,
    random_group_code,
)


def test_random_group_code() -> None:
    code = random_group_code()
    assert len(code) == 11  # 3-3-3 with two dashes
    assert is_valid_group_code(code)


def test_is_valid_group_code() -> None:
    assert is_valid_group_code('ABC-DEF-GHI') is True
    assert is_valid_group_code('ABCDEFGHI') is True
    assert is_valid_group_code('abc-def-ghi') is False
    assert is_valid_group_code('too-short') is False


def test_num_range_codec() -> None:
    assert num_range_decode('5-10') == (5, 10)
    assert num_range_encode((5, 10)) == '5-10'
    # inverted range is invalid
    assert num_range_decode('10-5') is None
    assert num_range_decode('not a range') is None
    assert num_range_decode(42) is None


def test_date_range_codec() -> None:
    decoded = date_range_decode('2020-01-01:2020-12-31')
    assert decoded == (date(2020, 1, 1), date(2020, 12, 31))

    assert date_range_encode(
        (date(2020, 1, 1), date(2020, 12, 31))) == '2020-01-01:2020-12-31'

    assert date_range_decode('garbage') is None
    assert date_range_decode(None) is None


def test_is_internal_image() -> None:
    internal = 'https://example.org/storage/' + 'a' * 64
    assert is_internal_image(internal) is True
    assert is_internal_image('https://example.org/external.jpg') is False
    assert is_internal_image(None) is False


def test_extract_thumbnail() -> None:
    assert extract_thumbnail(None) is None
    assert extract_thumbnail('<p>no image</p>') is None

    internal = 'https://example.org/storage/' + 'a' * 64
    html = f'<p><img src="{internal}"></p>'
    assert extract_thumbnail(html) == internal + '/thumbnail'

    external = 'https://example.org/pic.jpg'
    assert extract_thumbnail(f'<p><img src="{external}"></p>') == external


def test_extract_municipality() -> None:
    assert extract_municipality(None) is None
    assert extract_municipality('no municipality here') is None
    assert extract_municipality('Street 1, 6000 Luzern') == (6000, 'Luzern')


def test_dates_overlap() -> None:
    a = [(datetime(2020, 1, 1, 10), datetime(2020, 1, 1, 12))]
    overlapping = [(datetime(2020, 1, 1, 11), datetime(2020, 1, 1, 13))]
    adjacent = [(datetime(2020, 1, 1, 12), datetime(2020, 1, 1, 13))]

    assert dates_overlap(a, overlapping) is True
    # touching at the boundary does not count as overlap
    assert dates_overlap(a, adjacent) is False
