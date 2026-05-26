from __future__ import annotations

import pytest

from onegov.swissvotes.converters import policy_area_decode
from onegov.swissvotes.converters import policy_area_encode
from onegov.swissvotes.models import PolicyArea


def test_policy_area_decode() -> None:
    assert policy_area_decode('1') == PolicyArea('1')
    assert policy_area_decode('1.12') == PolicyArea('1.12')
    assert policy_area_decode('1.12.121') == PolicyArea('1.12.121')
    assert policy_area_decode('4.42.421') == PolicyArea('4.42.421')
    assert policy_area_decode('10.102') == PolicyArea('10.102')
    assert policy_area_decode('10.103.1035') == PolicyArea('10.103.1035')
    assert policy_area_decode('12.125.1251') == PolicyArea('12.125.1251')

    with pytest.raises(ValueError):
        policy_area_decode('')
    with pytest.raises(ValueError):
        policy_area_decode('1.12.123.1231')  # too many levels
    with pytest.raises(ValueError):
        policy_area_decode('z')
    with pytest.raises(ValueError):
        policy_area_decode('1,12,121')
    with pytest.raises(ValueError):
        policy_area_decode('1.32.121')
    with pytest.raises(ValueError):
        policy_area_decode('4.92.421')
    with pytest.raises(ValueError):
        policy_area_decode('a.a2.a21')


def test_policy_area_encode() -> None:
    assert policy_area_encode(None) == ''
    assert policy_area_encode(PolicyArea('1')) == '1'
    assert policy_area_encode(PolicyArea('1.12')) == '1.12'
    assert policy_area_encode(PolicyArea('1.12.121')) == '1.12.121'
