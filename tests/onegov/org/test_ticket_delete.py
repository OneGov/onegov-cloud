import os
from onegov.org.models.ticket import FormSubmissionHandler, TicketDeletionMixin
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


class EchoHandler(Handler, TicketDeletionMixin):
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

    def prepare_delete_ticket(self):

        """The handler knows best what to do when a ticket is called for
        deletion. """
        return


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


def test_ticket_deleted_submission_is_resilient(client):
    # it so happened that the ticket.handler.submission was None
    # Viewing a ticket should not break this if that is the case.

    client.login_editor()

    page = client.get('/forms/new')
    page.form['title'] = "Newsletter"
    page.form['definition'] = "E-Mail *= @@@"
    page.form.submit()

    page = client.get('/form/newsletter')
    page.form['e_mail'] = 'info@seantis.ch'

    page.form.submit().follow().form.submit().follow()
    assert len(os.listdir(client.app.maildir)) == 1
    assert len(client.get('/timeline/feed').json['messages']) == 1

    page = client.get('/tickets/ALL/open')
    page.click('Annehmen')
    page.click('Annehmen')
    ticket_page = page.click('Annehmen').follow()

    ticket_url = ticket_page.request.path

    _, _, found_attrs = ticket_page._find_element(
        tag='a',
        href_attr='href',
        href_extract=None,
        content='Ticket abschliessen',
        id=None,
        href_pattern=None,
        index=None,
        verbose=False,
    )

    ticket_close_url = str(found_attrs['uri'])

    # intentionally call this twice, as this happened actually
    client.get(ticket_close_url).follow()
    client.get(ticket_close_url).follow()

    # reopen
    client.login_admin()
    ticket_page = client.get(ticket_url)
    ticket_page.click('Ticket wieder öffnen').follow()

    session = client.app.session()

    ticket = session.query(Ticket).first()
    session.delete(ticket.handler.submission)

    transaction.commit()
    ticket = session.query(Ticket).first()

    # monkey patch the property
    ticket.handler.__dict__['deleted'] = True

    session.add(ticket)
    transaction.commit()

    ticket = session.query(Ticket).first()
    assert ticket.handler.submission is None
    assert ticket.handler.deleted
    assert isinstance(ticket.handler, FormSubmissionHandler)

    # now navigate to ticket submission is None
    ticket_url = ticket_close_url[:-6]
    assert client.get(ticket_url).status_code == 200
