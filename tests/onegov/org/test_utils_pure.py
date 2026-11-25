from __future__ import annotations

from datetime import datetime, time
from onegov.org.utils import (
    COLORS,
    complete_url,
    djb2_hash,
    event_color,
    extract_categories_and_subcategories,
    format_phone_number,
    get_extension_color,
    get_user_color,
    narrowest_access,
    render_time_range,
    widest_access,
)


def test_djb2_hash_is_bounded_and_stable() -> None:
    assert 0 <= djb2_hash('hello', 100) < 100
    assert djb2_hash('hello', 100) == djb2_hash('hello', 100)


def test_user_and_extension_colors() -> None:
    assert get_user_color('user-a').startswith('#')
    assert len(get_user_color('user-a')) == 7
    # deterministic per input
    assert get_user_color('user-a') == get_user_color('user-a')
    assert get_extension_color('pdf').startswith('#')


def test_event_color_is_from_palette() -> None:
    color = event_color('Brand')
    assert color in COLORS
    # stable for the same input
    assert event_color('Brand') == color


def test_render_time_range() -> None:
    assert render_time_range(time(9, 0), time(17, 30)) == '09:00 - 17:30'
    # midnight end renders as 24:00
    assert render_time_range(time(9, 0), time(0, 0)) == '09:00 - 24:00'
    assert render_time_range(
        time(9, 0), time(23, 59, 59, 999999)) == '09:00 - 24:00'
    # a datetime end is reduced to its time
    assert render_time_range(
        time(8, 0), datetime(2020, 1, 1, 12, 15)) == '08:00 - 12:15'


def test_complete_url() -> None:
    assert complete_url(None) is None
    assert complete_url('https://') is None
    assert complete_url('https://keine') is None
    assert complete_url('http://example.org') == 'http://example.org'
    assert complete_url('/local') == '/local'
    assert complete_url('example.org') == 'https://example.org'


def test_widest_and_narrowest_access() -> None:
    assert widest_access('private', 'public') == 'public'
    assert widest_access('public', 'private') == 'public'
    assert widest_access('private', 'member') == 'member'

    assert narrowest_access('private', 'public') == 'private'
    assert narrowest_access('public', 'member') == 'member'

    # unknown values are ignored
    assert widest_access('bogus', 'member') == 'member'


def test_extract_categories_and_subcategories() -> None:
    from collections.abc import Mapping, Sequence

    categories: Sequence[Mapping[str, Sequence[str] | None] | str] = [
        'main_1',
        {'main_2': ['sub_21', 'sub_22']},
        {'main_3': None},
    ]

    cats, sub_cats = extract_categories_and_subcategories(categories)
    assert cats == ['main_1', 'main_2', 'main_3']
    assert sub_cats == [[], ['sub_21', 'sub_22'], []]

    flat = extract_categories_and_subcategories(categories, flattened=True)
    assert flat == ['main_1', 'main_2', 'main_3', 'sub_21', 'sub_22']

    assert extract_categories_and_subcategories([]) == ([], [])


def test_format_phone_number() -> None:
    assert format_phone_number('') == ''
    assert format_phone_number('0791234567') == '+41 79 123 45 67'
    # unparseable input is returned unchanged
    assert format_phone_number('not a number') == 'not a number'
