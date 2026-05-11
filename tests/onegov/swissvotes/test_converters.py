from __future__ import annotations

from onegov.swissvotes.converters import policy_area_decode
from onegov.swissvotes.converters import policy_area_encode
from onegov.swissvotes.models import PolicyArea


def test_policy_area_decode() -> None:
    assert policy_area_decode('') is None
    assert policy_area_decode('1') == PolicyArea('1')
    assert policy_area_decode('1.12') == PolicyArea('1.12')
    assert policy_area_decode('1.12.121') == PolicyArea('1.12.121')
    assert policy_area_decode('4.42.421') == PolicyArea('4.42.421')
    assert policy_area_decode('10.102') == PolicyArea('10.102')
    assert policy_area_decode('10.103.1035') == PolicyArea('10.103.1035')
    assert policy_area_decode('12.125.1251') == PolicyArea('12.125.1251')
    assert policy_area_decode('1.12.123.1231') == PolicyArea('1.12.123.1231')

    # invalid policy areas
    assert policy_area_decode('z') is None
    assert policy_area_decode('1,12,121') is None
    assert policy_area_decode('1.32.121') is None
    assert policy_area_decode('4.92.421') is None
    assert policy_area_decode('a.a2.a21') is None


def test_policy_area_encode() -> None:
    assert policy_area_encode(None) == ''
    assert policy_area_encode(PolicyArea('1')) == '1'
    assert policy_area_encode(PolicyArea('1.12')) == '1.12'
    assert policy_area_encode(PolicyArea('1.12.121')) == '1.12.121'
