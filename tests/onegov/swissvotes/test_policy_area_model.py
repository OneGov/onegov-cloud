from __future__ import annotations

import pytest

from decimal import Decimal
from onegov.swissvotes.models.policy_area import PolicyArea


def test_init_variants() -> None:
    assert PolicyArea('1.12.121').value == '1.12.121'
    assert PolicyArea([1, 12, 121]).value == '1.12.121'
    # a decimal with a level constructs a value string
    assert isinstance(PolicyArea(Decimal('1.12'), 2).value, str)

    with pytest.raises(NotImplementedError):
        PolicyArea(3.5)  # type: ignore[call-overload]


def test_from_url_param_valid() -> None:
    for param in ('1', '1.12', '1.12.121'):
        result = PolicyArea.from_url_param(param)
        assert result is not None
        assert result.value == param


def test_from_url_param_invalid() -> None:
    assert PolicyArea.from_url_param('') is None
    assert PolicyArea.from_url_param('abc') is None
    # more than three components
    assert PolicyArea.from_url_param('1.12.121.1211') is None
    # a component not starting with the previous one
    assert PolicyArea.from_url_param('1.99') is None


def test_dunder_methods() -> None:
    area = PolicyArea('1.12')
    assert repr(area) == '1.12'
    assert area == PolicyArea('1.12')
    assert area != PolicyArea('1.13')
    assert area != 'not a policy area'
    # hashable and equal hashes for equal values
    assert hash(area) == hash(PolicyArea('1.12'))
    assert len({area, PolicyArea('1.12')}) == 1


def test_descriptors() -> None:
    area = PolicyArea('1.12.121')
    assert area.level == 3
    assert area.descriptor == 121
    assert area.descriptor_path == [1, 12, 121]
    assert area.descriptor_decimal == Decimal(121) / 100


def test_label_path() -> None:
    labels = PolicyArea('1').label_path
    assert isinstance(labels, list)
    assert labels
    assert all(isinstance(label, str) for label in labels)
