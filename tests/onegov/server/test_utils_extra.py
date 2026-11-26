from __future__ import annotations

from collections import OrderedDict
from onegov.server.utils import load_class, patch_morepath


def test_load_class_from_class() -> None:
    assert load_class(OrderedDict) is OrderedDict


def test_load_class_from_string() -> None:
    assert load_class('collections.OrderedDict') is OrderedDict


def test_load_class_missing_attribute() -> None:
    assert load_class('collections.DefinitelyNotAClass') is None


def test_patch_morepath_is_idempotent() -> None:
    patch_morepath()
    patch_morepath()  # second call returns early

    import morepath.autosetup
    assert morepath.autosetup._onegov_patch is True  # type: ignore[attr-defined]
