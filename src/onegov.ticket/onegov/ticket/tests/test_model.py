import pytest

from datetime import timedelta
from freezegun import freeze_time
from onegov.ticket import Ticket
from onegov.ticket.errors import InvalidStateChange
from onegov.user.model import User
from sedate import utcnow


def test_transitions(session):

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
    assert ticket.state == 'pending'
    assert ticket.user == user

    ticket.accept_ticket(user)  # idempotent..
    assert ticket.state == 'pending'
    assert ticket.user == user

    with pytest.raises(InvalidStateChange):
        ticket.accept_ticket(User())  # ..unless it's another user

    ticket.reopen_ticket(user)  # idempotent as well -> would lead to no change
    assert ticket.state == 'pending'
    assert ticket.user == user

    ticket.close_ticket()
    assert ticket.state == 'closed'
    assert ticket.user == user

    ticket.close_ticket()  # idempotent
    assert ticket.state == 'closed'
    assert ticket.user == user

    with pytest.raises(InvalidStateChange):
        ticket.accept_ticket(user)

    another_user = User()
    ticket.reopen_ticket(another_user)
    assert ticket.state == 'pending'
    assert ticket.user is another_user

    ticket.reopen_ticket(another_user)  # idempotent..
    assert ticket.state == 'pending'
    assert ticket.user is another_user

    with pytest.raises(InvalidStateChange):
        ticket.reopen_ticket(user)  # ..unless it's another user


def test_process_time(session):

    user = User()

    with freeze_time('2016-06-21') as frozen:

        # the created timestamp would usually be set as the session is flushed
        ticket = Ticket(state='open', created=Ticket.timestamp())

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is 0
        assert ticket.last_state_change is None

        frozen.tick(delta=timedelta(seconds=10))

        assert ticket.reaction_time is None
        assert ticket.process_time is None
        assert ticket.current_process_time is 10
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


def test_legacy_process_time(session):
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
