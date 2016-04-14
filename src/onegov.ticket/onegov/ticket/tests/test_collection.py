from unittest.mock import Mock
from onegov.ticket import Handler, Ticket, TicketCollection


class EchoHandler(Handler):

    @property
    def deleted(self):
        return False

    @property
    def email(self):
        return self.data.get('email')

    @property
    def title(self):
        return self.data.get('title')

    @property
    def subtitle(self):
        return self.data.get('subtitle')

    @property
    def group(self):
        return self.data.get('group')

    def get_summary(self, request):
        return self.data.get('summary')

    def get_links(self, request):
        return self.data.get('links')


class LimitingHandler(Handler):

    @property
    def deleted(self):
        return False

    @property
    def title(self):
        return 'Foo'

    @property
    def subtitle(self):
        return '0xdeadbeef'

    @property
    def group(self):
        return 'Bar'

    @property
    def handler_id(self):
        return 1

    @property
    def handler_data(self):
        return {}

    @property
    def email(self):
        return 'foo@bar.com'

    def get_summary(self, request):
        return 'foobar'

    @classmethod
    def handle_extra_parameters(cls, session, query, extra_parameters):
        if 'limit' in extra_parameters:
            return query.limit(extra_parameters['limit'])
        else:
            return query


class ABCTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'ABC'}
    es_type_name = 'abc_tickets'


class FooTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FOO'}
    es_type_name = 'foo_tickets'


class BarTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'BAR'}
    es_type_name = 'bar_tickets'


class EcoTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'ECO'}
    es_type_name = 'bar_tickets'


class LtdTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'LTD'}
    es_type_name = 'ltd_tickets'


def test_random_number():

    collection = TicketCollection(session=object())
    assert 10000000 <= collection.random_number(length=8) <= 99999999


def test_random_ticket_number():

    collection = TicketCollection(session=object())

    collection.random_number = Mock(return_value=10000000)
    assert collection.random_ticket_number('ABC') == 'ABC-1000-0000'

    collection.random_number = Mock(return_value=99999999)
    assert collection.random_ticket_number('XXX') == 'XXX-9999-9999'


def test_issue_unique_ticket_number(session, handlers):

    handlers.register('ABC', EchoHandler)
    collection = TicketCollection(session)

    collection.random_number = Mock(return_value=10000000)
    assert collection.issue_unique_ticket_number('ABC') == 'ABC-1000-0000'

    session.add(Ticket(
        number='ABC-1000-0000',
        title='Test',
        group='Test',
        handler_code='ABC',
        handler_id='1'
    ))

    collection.random_number = Mock(side_effect=[10000000, 10000001, 10000002])
    assert collection.issue_unique_ticket_number('ABC') == 'ABC-1000-0001'
    assert collection.issue_unique_ticket_number('ABC') == 'ABC-1000-0002'
    assert len(collection.random_number.mock_calls) == 3


def test_ticket_count(session):

    for i in range(0, 3):
        i = i + 1
        session.add(Ticket(
            number='ABC-1000-{:04d}'.format(i),
            title='test', group='test',
            handler_code='ABC',
            handler_id=str(i),
            state='open'
        ))

    for i in range(0, 2):
        i = (i + 1) * 10
        session.add(Ticket(
            number='ABC-1000-{:04d}'.format(i),
            title='test', group='test',
            handler_code='ABC',
            handler_id=str(i),
            state='pending'
        ))

    for i in range(0, 1):
        i = (i + 1) * 100
        session.add(Ticket(
            number='ABC-1000-{:04d}'.format(i),
            title='test', group='test',
            handler_code='ABC',
            handler_id=str(i),
            state='closed'
        ))

    count = TicketCollection(session).get_count()
    assert count.open == 3
    assert count.pending == 2
    assert count.closed == 1

    assert TicketCollection(session).for_state('all').subset().count() == 6


def test_handler_subset(session):
    session.add(Ticket(
        number='FOO-1000-0001',
        title='test', group='test',
        handler_code='FOO',
        handler_id='1',
        state='open'
    ))

    session.add(Ticket(
        number='BAR-1000-0001',
        title='test', group='test',
        handler_code='BAR',
        handler_id='2',
        state='open'
    ))

    assert TicketCollection(session).subset().count() == 2
    assert TicketCollection(session, handler='BAR').subset().count() == 1
    assert TicketCollection(session, handler='FOO').subset().count() == 1


def test_open_ticket(session, handlers):

    handlers.register('ECO', EchoHandler)

    collection = TicketCollection(session)

    ticket = collection.open_ticket(
        handler_id='1',
        handler_code='ECO',
        title="Title",
        subtitle="Subtitle",
        group="Group",
        summary="Summary",
        links=[("Link", '#')],
        email="citizen@example.org"
    )

    assert ticket.number.startswith('ECO-')
    assert ticket.title == "Title"
    assert ticket.group == "Group"
    assert ticket.handler_id == '1'
    assert ticket.handler_code == 'ECO'
    assert ticket.handler_data == {
        'title': "Title",
        'subtitle': "Subtitle",
        'group': "Group",
        'summary': "Summary",
        'links': [("Link", '#')],
        'email': "citizen@example.org"
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
    assert collection.by_handler_id('1') is not None


def test_snapshot_ticket(session, handlers):

    @handlers.registered_handler('FOO')
    class FooHandler(Handler):

        @property
        def deleted(self):
            return False

        @property
        def title(self):
            return 'Foo'

        @property
        def subtitle(self):
            return '0xdeadbeef'

        @property
        def group(self):
            return 'Bar'

        @property
        def handler_id(self):
            return 1

        @property
        def handler_data(self):
            return {}

        @property
        def email(self):
            return 'foo@bar.com'

        def get_summary(self, request):
            return 'foobar'

    collection = TicketCollection(session)

    ticket = collection.open_ticket(
        handler_id='1',
        handler_code='FOO'
    )

    ticket.create_snapshot(request=object())
    assert ticket.snapshot['email'] == 'foo@bar.com'
    assert ticket.snapshot['summary'] == 'foobar'


def test_handle_extra_options(session, handlers):

    handlers.register('LTD', LimitingHandler)

    collection = TicketCollection(session)
    collection.handlers = handlers

    collection.open_ticket(handler_id='1', handler_code='LTD')
    collection.open_ticket(handler_id='2', handler_code='LTD')
    collection.open_ticket(handler_id='3', handler_code='LTD')

    assert collection.subset().count() == 3

    collection.extra_parameters = {'limit': 1}
    assert collection.subset().count() == 3

    collection.handler = 'LTD'
    assert collection.subset().count() == 1

    collection.extra_parameters = {'limit': 2}
    assert collection.subset().count() == 2


def test_available_groups(session):
    session.add(Ticket(
        number='FOO-1000-0001',
        title='test', group='one',
        handler_code='FOO',
        handler_id='1',
        state='open'
    ))

    session.add(Ticket(
        number='BAR-1000-0001',
        title='test', group='two',
        handler_code='BAR',
        handler_id='2',
        state='open'
    ))

    collection = TicketCollection(session)

    assert collection.subset().count() == 2
    assert collection.for_group('one').subset().count() == 1
    assert collection.for_group('two').subset().count() == 1
    assert collection.available_groups() == ('one', 'two')
    assert collection.for_group('one').available_groups() == ('one', 'two')
    assert collection.for_group('two').available_groups() == ('one', 'two')
    assert collection.available_groups('FOO') == ('one', )
    assert collection.available_groups('BAR') == ('two', )
