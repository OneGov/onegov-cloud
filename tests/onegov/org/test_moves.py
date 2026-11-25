from __future__ import annotations

import pytest

from onegov.form import FormDefinition
from onegov.org.models.page_move import PageMove
from onegov.org.models.person_move import (
    FormPersonMove,
    PagePersonMove,
    PersonMove,
    ResourcePersonMove,
)
from onegov.page import Page
from onegov.reservation import Resource
from types import SimpleNamespace
from unittest.mock import Mock


from typing import Any


def _obj(**kwargs: Any) -> Any:
    return SimpleNamespace(**kwargs)


def test_person_move_strips_dashes() -> None:
    move = PersonMove(None, _obj(content={}), 'a-b-c', 'd-e-f', 'above')  # type: ignore[arg-type]
    assert move.subject == 'abc'
    assert move.target == 'def'


def test_person_move_is_valid() -> None:
    obj = _obj(content={'people': [('abc', ()), ('def', ())]})

    assert PersonMove(None, obj, 'abc', 'def', 'above').is_valid() is True  # type: ignore[arg-type]
    # same subject and target
    assert PersonMove(None, obj, 'abc', 'abc', 'above').is_valid() is False  # type: ignore[arg-type]
    # no people at all
    assert PersonMove(
        None, _obj(content={}), 'abc', 'def', 'above').is_valid() is False  # type: ignore[arg-type]
    # only one of the two present
    one = _obj(content={'people': [('abc', ())]})
    assert PersonMove(None, one, 'abc', 'def', 'above').is_valid() is False  # type: ignore[arg-type]


def test_person_move_get_implementation() -> None:
    assert PersonMove.get_implementation(Mock(spec=Page)) is PagePersonMove
    assert PersonMove.get_implementation(
        Mock(spec=FormDefinition)) is FormPersonMove
    assert PersonMove.get_implementation(
        Mock(spec=Resource)) is ResourcePersonMove
    with pytest.raises(NotImplementedError):
        PersonMove.get_implementation(object())


def test_person_move_get_key() -> None:
    form = Mock(spec=FormDefinition)
    form.name = 'my-form'
    assert PersonMove.get_key(form) == 'my-form'
    assert PersonMove.get_key(_obj(id=5)) == 5


def test_page_move_ids() -> None:
    move = PageMove(None, _obj(id=1), _obj(id=2), 'above')  # type: ignore[arg-type]
    assert move.subject_id == 1
    assert move.target_id == 2
