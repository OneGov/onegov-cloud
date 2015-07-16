import pytest

from onegov.ticket import Ticket
from onegov.user.model import User


def test_transitions(session):

    ticket = Ticket(state='open')
    assert ticket.state == 'open'
    assert ticket.user is None

    user = User()

    with pytest.raises(AssertionError):
        ticket.close_ticket()
    with pytest.raises(AssertionError):
        ticket.reopen_ticket(user)

    ticket.accept_ticket(user)
    assert ticket.state == 'pending'
    assert ticket.user == user

    with pytest.raises(AssertionError):
        ticket.accept_ticket(user)
    with pytest.raises(AssertionError):
        ticket.reopen_ticket(user)

    ticket.close_ticket()
    assert ticket.state == 'closed'
    assert ticket.user == user

    with pytest.raises(AssertionError):
        ticket.accept_ticket(user)
    with pytest.raises(AssertionError):
        ticket.close_ticket()

    ticket.reopen_ticket(User())
    assert ticket.state == 'pending'
    assert ticket.user != user
    assert ticket.user is not None
