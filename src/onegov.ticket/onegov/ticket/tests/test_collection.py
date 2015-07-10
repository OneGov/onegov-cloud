from mock import Mock
from onegov.ticket import Handler, Ticket, TicketCollection


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


def test_open_ticket(session, handlers):

    @handlers.registered_handler('ECO')
    class EchoHandler(Handler):

        @property
        def title(self):
            return self.data.get('title')

        @property
        def group(self):
            return self.data.get('group')

        def get_summary(self, request):
            return self.data.get('summary')

        def get_links(self, request):
            return self.data.get('links')

    collection = TicketCollection(session)

    ticket = collection.open_ticket(
        handler_code='ECO',
        title="Title",
        group="Group",
        summary="Summary",
        links=[("Link", '#')]
    )

    assert ticket.number.startswith('ECO-')
    assert ticket.title == "Title"
    assert ticket.group == "Group"
    assert ticket.handler_code == 'ECO'
    assert ticket.handler_data == {
        'title': "Title",
        'group': "Group",
        'summary': "Summary",
        'links': [("Link", '#')]
    }

    assert ticket.handler.get_summary(request=object()) == "Summary"
    assert ticket.handler.get_links(request=object()) == [("Link", '#')]

    ticket.handler_data['title'] = "Test"
    assert ticket.title == "Title"
    ticket.handler.refresh()
    assert ticket.title == "Test"

    assert len(collection.by_handler_code("ECO")) == 1
    assert collection.by_id(ticket.id)
    assert collection.by_id(ticket.id, ensure_handler_code='FOO') is None
