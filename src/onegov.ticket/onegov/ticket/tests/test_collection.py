from mock import Mock
from onegov.ticket import Ticket, TicketCollection


def test_random_number():

    collection = TicketCollection(session=object())
    assert 10000000 <= collection.random_number(length=8) <= 99999999


def test_random_ticket_number():

    collection = TicketCollection(session=object())

    collection.random_number = Mock(return_value=10000000)
    assert collection.random_ticket_number('ABC') == 'ABC-1000-0000'

    collection.random_number = Mock(return_value=99999999)
    assert collection.random_ticket_number('XXX') == 'XXX-9999-9999'


def test_issue_unique_ticket_number(session):

    collection = TicketCollection(session)

    collection.random_number = Mock(return_value=10000000)
    assert collection.issue_unique_ticket_number('ABC') == 'ABC-1000-0000'

    session.add(Ticket(
        number='ABC-1000-0000',
        title='Test',
        group='Test',
        handler_code='ABC',
    ))

    collection.random_number = Mock(side_effect=[10000000, 10000001, 10000002])
    assert collection.issue_unique_ticket_number('ABC') == 'ABC-1000-0001'
    assert collection.issue_unique_ticket_number('ABC') == 'ABC-1000-0002'
    assert len(collection.random_number.mock_calls) == 3
