from __future__ import annotations
import pytest

from onegov.translator_directory.utils import out_of_tolerance


@pytest.mark.parametrize('old,new,factor,maxtol,outcome', [
    (None, 5, 0.1, 5, False),
    (5.0, 5, 0.1, 0, False),
    (5.0, 5.5, 0.1, 0, True),
    (5.0, 5.5, 0.1, 1, False),
    (5.0, 5.51, 0.1, 1, False),
    (5.0, 5.51, 0.1, .5, True),
])
def test_out_of_tolerance(
    old: float | None,
    new: float,
    factor: float,
    maxtol: float,
    outcome: bool
) -> None:
    assert out_of_tolerance(old, new, factor, maxtol) == outcome
