import transaction
from datetime import datetime
from onegov.core.utils import Bunch
from onegov.ticket import TicketCollection, Handler, Ticket
from onegov.user import UserCollection
from sedate import ensure_timezone
from tests.shared import Client as BaseClient


class Client(BaseClient):
    skip_n_forms = 1


# This is used implicitly to check for polymorphic identity
class EchoTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'EHO'}
    es_type_name = 'echo_tickets'


class EchoHandler(Handler):
    handler_title = "Echo"

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


def register_echo_handler(handlers):
    handlers.register('EHO', EchoHandler)


def archive_all_tickets(session, tickets, tz):
    request = Bunch(client_addr='127.0.0.1')
    UserCollection(session).register('b', 'p@ssw0rd', request, role='admin')
    users = UserCollection(session).query().all()
    user = users[0]
    for t in tickets:
        t.created = datetime(2016, 1, 2, 10, tzinfo=tz)
        t.accept_ticket(user)
        t.close_ticket()
        t.archive_ticket()
        t.modified = datetime(2016, 1, 2, 10, tzinfo=tz)


def test_ticket_archived_manual_delete(org_app, handlers):
    register_echo_handler(handlers)

    client = Client(org_app)
    tz = ensure_timezone('Europe/Zurich')

    transaction.begin()

    session = org_app.session()
    collection = TicketCollection(session)

    tickets = [
        collection.open_ticket(
            handler_id='1',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='2',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='3',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='4',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='5',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='6',
            handler_code='EHO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
    ]

    archive_all_tickets(session, tickets, tz)
    transaction.commit()

    client.login_admin()
    client.get('/tickets-archive/ALL')

    assert session.query(Ticket).filter_by(state='archived').count() == len(
        tickets)
    client.delete('/tickets-archive/ALL/delete')
    assert session.query(Ticket).filter_by(state='archived').count() == 0

    # todo: try what happens if you access a link that was deleted
