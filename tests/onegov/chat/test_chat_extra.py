from __future__ import annotations

import pytest

from onegov.chat import Message
from onegov.chat.collections import ChatCollection, TextModuleCollection
from onegov.chat.models import Chat, TextModule
from onegov.chat.utils import param_from_path
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# --- utils --------------------------------------------------------------


def test_param_from_path() -> None:
    assert param_from_path(
        'schema', '/chats?schema=onegov_town6-meggen'
    ) == 'onegov_town6-meggen'


def test_param_from_path_missing() -> None:
    with pytest.raises(ValueError):
        param_from_path('schema', '/chats?foo=bar')


def test_param_from_path_multiple() -> None:
    with pytest.raises(ValueError):
        param_from_path('schema', '/chats?schema=a&schema=b')


# --- text module model / collection -------------------------------------


def test_text_module_properties() -> None:
    shared = TextModule(name='greeting', text='Hello\nWorld')
    assert shared.private is False

    private = TextModule(name='p', text='x', user_id=uuid4())
    assert private.private is True

    # formatted text is linkified / paragraphified
    assert 'Hello' in shared.formatted_text

    # preview collapses multi-line / long text
    assert shared.preview_text == 'Hello ...'

    short = TextModule(name='s', text='Just one line')
    assert short.preview_text == 'Just one line'

    long = TextModule(name='l', text='x' * 60)
    assert long.preview_text.endswith(' ...')
    assert len(long.preview_text) == 50


def test_text_module_collection_filters(session: Session) -> None:
    from onegov.user import User

    user = User(username='owner@example.org', password='x', role='member')
    session.add(user)
    session.flush()
    owner = user.id

    session.add_all((
        TextModule(name='shared', text='t'),
        TextModule(name='mine', text='t', user_id=owner),
        TextModule(name='typed', text='t', message_type='ticket'),
        TextModule(name='handled', text='t', handler_code='FRM'),
    ))
    session.flush()

    # default: only shared (user_id is None) modules
    assert TextModuleCollection(session).query().count() == 3

    # owner sees their own plus the shared ones
    assert TextModuleCollection(session, owner=str(owner)).query().count() == 4

    # type filter
    typed = TextModuleCollection(session, type='ticket', owner=str(owner))
    assert typed.query().count() == 1

    # handler filter
    handled = TextModuleCollection(
        session, handler='FRM', owner=str(owner))
    assert handled.query().count() == 1


# --- chat collection ----------------------------------------------------


def _chat(session: Session, **kwargs: object) -> Chat:
    chats = ChatCollection(session)
    return chats.add(
        customer_name=kwargs.pop('customer_name', 'User A'),  # type: ignore[arg-type]
        email=kwargs.pop('email', 'user@example.org'),  # type: ignore[arg-type]
        topic=kwargs.pop('topic', 'help'),  # type: ignore[arg-type]
    )


def test_chat_collection_add(session: Session) -> None:
    chats = ChatCollection(session)
    chat = chats.add('User A', 'user@example.org', 'help')
    assert chat.customer_name == 'User A'
    assert chat.active is True
    assert chats.query().count() == 1


def test_chat_collection_subset_states(session: Session) -> None:
    active = _chat(session)
    active.chat_history = [{'text': 'hi'}]
    archived = _chat(session)
    archived.chat_history = [{'text': 'bye'}]
    archived.active = False
    # a chat with empty history is excluded from every subset
    _chat(session)
    session.flush()

    assert ChatCollection(session, state='active').subset().count() == 1
    assert ChatCollection(session, state='archived').subset().count() == 1
    assert ChatCollection(session, state='all').subset().count() == 2


def test_chat_collection_misc(session: Session) -> None:
    chats = ChatCollection(session, state='archived')
    assert chats.name_of_view == 'archive'
    assert chats.page_index == 0

    other = chats.page_by_index(3)
    assert other.page == 3
    assert other.state == 'archived'

    assert ChatCollection(session) == ChatCollection(session)
    assert ChatCollection(session) != ChatCollection(session, page=1)
    assert ChatCollection(session) != object()


# --- message model ------------------------------------------------------


def test_message_subtype_and_get(session: Session) -> None:
    message = Message(text='hello', channel_id='c')
    assert message.subtype is None
    # get() returns the raw text for a generic message (request is unused)
    assert message.get(None) == 'hello'  # type: ignore[arg-type]


def test_message_equality(session: Session) -> None:
    message = Message(text='hello', channel_id='c')
    assert message != object()
