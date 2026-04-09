from __future__ import annotations

import pytest
import transaction

from datetime import timedelta
from freezegun import freeze_time
from onegov.ticket import Ticket
from onegov.ticket import TicketPermission
from onegov.ticket.errors import InvalidStateChange
from onegov.user import User
from onegov.user import UserGroup
from sedate import utcnow
from sqlalchemy.exc import IntegrityError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_transitions(session: Session) -> None:

    # the created timestamp would usually be set as the session is flushed
    ticket = Ticket(state='open', created=Ticket.timestamp())

    assert ticket.state == 'open'
    assert ticket.user is None

    user = User()

    with pytest.raises(InvalidStateChange):
        ticket.close_ticket()

    with pytest.raises(InvalidStateChange):
        ticket.reopen_ticket(user)

    ticket.accept_ticket(user)
    # undo mypy narrowing of state
    ticket2 = ticket
    assert ticket2.state == 'pending'
    assert ticket.user == user

    ticket.accept_ticket(user)  # idempotent..
    assert ticket2.state == 'pending'
    assert ticket.user == user

    with pytest.raises(InvalidStateChange):
        ticket.accept_ticket(User())  # ..unless it's another user

    ticket.reopen_ticket(user)  # idempotent as well -> would lead to no change
    assert ticket2.state == 'pending'
    assert ticket.user == user

    # undo mypy narrowing of state
    ticket2 = ticket
    ticket.close_ticket()
    assert ticket2.state == 'closed'
    assert ticket.user == user

    ticket.close_ticket()  # idempotent
    assert ticket2.state == 'closed'
    assert ticket.user == user

    with pytest.raises(InvalidStateChange):
        ticket.accept_ticket(user)

    # undo mypy narrowing of state
    ticket2 = ticket
    another_user = User()
    ticket.reopen_ticket(another_user)
    assert ticket2.state == 'pending'
    assert ticket2.user is another_user

    ticket.reopen_ticket(another_user)  # idempotent..
    assert ticket2.state == 'pending'
    assert ticket2.user is another_user

    with pytest.raises(InvalidStateChange):
        ticket.reopen_ticket(user)  # ..unless it's another user


def test_process_time(session: Session) -> None:

    user = User()

    with freeze_time('2016-06-21') as frozen:

        # the created timestamp would usually be set as the session is flushed
        ticket = Ticket(state='open', created=Ticket.timestamp())

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time == 0
        assert ticket.last_state_change is None

        frozen.tick(delta=timedelta(seconds=10))

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time == 10
        assert ticket.last_state_change is None

        ticket.accept_ticket(user)

        assert ticket.reaction_time == 10
        assert ticket.process_time is None
        assert ticket.current_process_time == 0
        assert ticket.last_state_change == utcnow()

        frozen.tick(delta=timedelta(seconds=10))

        assert ticket.reaction_time == 10
        assert ticket.process_time is None
        assert ticket.current_process_time == 10
        assert ticket.last_state_change == utcnow() - timedelta(seconds=10)

        ticket.close_ticket()

        assert ticket.reaction_time == 10
        assert ticket.process_time == 10
        assert ticket.current_process_time == 10
        assert ticket.last_state_change == utcnow()

        frozen.tick(delta=timedelta(seconds=10))

        assert ticket.reaction_time == 10
        assert ticket.process_time == 10
        assert ticket.current_process_time == 10
        assert ticket.last_state_change == utcnow() - timedelta(seconds=10)

        ticket.reopen_ticket(user)

        assert ticket.reaction_time == 10
        assert ticket.process_time == 10
        assert ticket.current_process_time == 10
        assert ticket.last_state_change == utcnow()

        frozen.tick(delta=timedelta(seconds=10))

        assert ticket.reaction_time == 10
        assert ticket.process_time == 10
        assert ticket.current_process_time == 20
        assert ticket.last_state_change == utcnow() - timedelta(seconds=10)

        ticket.close_ticket()

        assert ticket.reaction_time == 10
        assert ticket.process_time == 20
        assert ticket.current_process_time == 20
        assert ticket.last_state_change == utcnow()


def test_legacy_process_time(session: Session) -> None:
    """ Tests the process_time/response_time for existing tickets, which cannot
    be migrated as this information cannot be inferred.

    """

    user = User()

    # test if the changes work for existing pending tickets (we don't need
    # to check the open tickets, as there is no difference between an open
    # ticket before/after the lead time introduction)
    with freeze_time('2016-06-21') as frozen:
        ticket = Ticket(state='pending', created=Ticket.timestamp(), user=user)

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change is None

        ticket.close_ticket()

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change == utcnow()

        frozen.tick(delta=timedelta(seconds=10))

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change == utcnow() - timedelta(seconds=10)

        ticket.reopen_ticket(user)

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change == utcnow()

        frozen.tick(delta=timedelta(seconds=10))

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change == utcnow() - timedelta(seconds=10)

        ticket.close_ticket()

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change == utcnow()

    # test if the changes work for existing closed tickets
    with freeze_time('2016-06-21') as frozen:
        ticket = Ticket(state='closed', created=Ticket.timestamp())

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change is None

        ticket.reopen_ticket(user)

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change == utcnow()

        frozen.tick(delta=timedelta(seconds=10))

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change == utcnow() - timedelta(seconds=10)

        ticket.close_ticket()

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is None
        assert ticket.last_state_change == utcnow()


def test_ticket_permission(session: Session) -> None:
    user_group = UserGroup(name='group')
    permission = TicketPermission(
        handler_code='PER', group=None, user_group=user_group
    )
    session.add(user_group)
    session.add(permission)
    session.flush()

    user_group = session.query(UserGroup).one()
    permission = session.query(TicketPermission).one()
    assert permission.handler_code == 'PER'
    assert permission.group is None
    assert permission.user_group == user_group

    session.delete(user_group)
    session.flush()
    assert session.query(TicketPermission).count() == 0


def test_ticket_permission_uniqueness(session: Session) -> None:
    user_group = UserGroup(name='group')
    permission = TicketPermission(
        handler_code='PER',
        group=None,
        user_group=user_group,
    )
    session.add(user_group)
    session.add(permission)
    session.flush()
    transaction.commit()
    transaction.begin()

    user_group = session.query(UserGroup).one()
    permission = session.query(TicketPermission).one()
    assert permission.handler_code == 'PER'
    assert permission.group is None
    assert permission.user_group == user_group

    # duplicate permission
    duplicate = TicketPermission(
        handler_code='PER',
        group=None,
        user_group=user_group,
    )
    session.add(duplicate)
    with pytest.raises(ValueError, match=r'Uniqueness violation'):
        session.flush()
    transaction.abort()
    transaction.begin()

    assert session.query(TicketPermission).count() == 1


def test_invalid_ticket_permission(session: Session) -> None:
    user_group = UserGroup(name='group')
    permission = TicketPermission(
        handler_code='PER',
        group=None,
        user_group=user_group,
        exclusive=False,
        immediate_notification=False,
    )
    session.add(user_group)
    session.add(permission)
    with pytest.raises(
        IntegrityError,
        match=r'check constraint "no_redundant_ticket_permissions"'
    ):
        transaction.commit()
