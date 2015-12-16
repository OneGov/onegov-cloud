import pytest

from onegov.ticket import Ticket
from onegov.ticket.errors import InvalidStateChange
from onegov.user.model import User


def test_transitions(session):

    ticket = Ticket(state='open')
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
