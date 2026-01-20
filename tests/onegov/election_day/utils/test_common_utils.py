from __future__ import annotations

from onegov.election_day.utils import get_parameter
from onegov.election_day.utils import replace_url
from pytest import raises


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    Bunch: type[Any]
else:
    from onegov.core.utils import Bunch


def test_get_param() -> None:

    with raises(NotImplementedError):
        get_parameter(Bunch(params={}), 'name', float, None)  # type: ignore[type-var]
    with raises(NotImplementedError):
        get_parameter(Bunch(params={}), 'name', tuple, None)  # type: ignore[type-var]
    with raises(NotImplementedError):
        get_parameter(Bunch(params={}), 'name', dict, None)  # type: ignore[type-var]

    assert get_parameter(Bunch(params={}), 'name', int, None) is None
    assert get_parameter(Bunch(params={}), 'name', int, 10) == 10
    assert get_parameter(Bunch(params={'name': ''}), 'name', int, 10) == 10
    assert get_parameter(Bunch(params={'name': 5}), 'name', int, 10) == 5
    assert get_parameter(Bunch(params={'name': '5'}), 'name', int, 10) == 5
    assert get_parameter(Bunch(params={'name': '  5 '}), 'name', int, 10) == 5

    assert get_parameter(Bunch(params={}), 'name', list, None) is None
    assert get_parameter(Bunch(params={}), 'name', list, [1, 2]) == [1, 2]
    assert get_parameter(
        Bunch(params={'name': ''}), 'name', list, [1, 2]) == [1, 2]
    assert get_parameter(
        Bunch(params={'name': 'a,b'}), 'name', list, None) == ['a', 'b']
    assert get_parameter(
        Bunch(params={'name': '  a,  b '}), 'name', list, 1) == ['a', 'b']

    assert get_parameter(Bunch(params={}), 'name', bool, None) is None
    assert get_parameter(Bunch(params={}), 'name', bool, False) is False
    assert get_parameter(
        Bunch(params={'name': ''}), 'name', bool, None) is None
    assert get_parameter(
        Bunch(params={'name': '1'}), 'name', bool, None) is True
    assert get_parameter(
        Bunch(params={'name': 'True'}), 'name', bool, None) is True
    assert get_parameter(
        Bunch(params={'name': 'trUe'}), 'name', bool, None) is True
    assert get_parameter(
        Bunch(params={'name': '  1 '}), 'name', bool, None) is True


def test_replace_url() -> None:
    assert replace_url(None, None) is None  # type: ignore[arg-type]
    assert replace_url(None, '') is None  # type: ignore[arg-type]
    assert replace_url('', '') == ''
    assert replace_url('', None) == ''
    assert replace_url('', 'https://b.y') == 'https://b.y'
    assert replace_url('http://a.x', 'https://b.y') == 'https://b.y'
    assert replace_url('http://a.x', 'https://') == 'https://a.x'
    assert replace_url('http://a.x/m', 'https://b.y') == 'https://b.y/m'
