import os
import textwrap
from webtest import Upload
from onegov.file import FileCollection
from onegov.form import FormCollection, FormSubmissionCollection
from onegov.org.models.ticket import FormSubmissionHandler
import transaction
from datetime import datetime
from onegov.core.utils import Bunch
from onegov.ticket import TicketCollection, Handler, Ticket
from onegov.user import UserCollection
from sedate import ensure_timezone
from tests.shared import Client as BaseClient


class Client(BaseClient):
    skip_n_forms = 1


class TicketDeletionMixin:

    @property
    def ticket_deletable(self):
        return self.ticket.state == 'archived'

    def prepare_delete_ticket(self):
        """The handler knows best what to do when a ticket is called for
        deletion. """
        assert self.ticket_deletable
        pass


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


# This is used implicitly to check for polymorphic identity
class EchoTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FOO'}
    es_type_name = 'frr_tickets'


def register_echo_handler(handlers):
    handlers.register('FOO', EchoHandler)


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


def test_delete_ticket_without_submission(org_app, handlers):
    register_echo_handler(handlers)

    client = Client(org_app)
    tz = ensure_timezone('Europe/Zurich')

    transaction.begin()

    session = org_app.session()
    collection = TicketCollection(session)

    tickets = [
        collection.open_ticket(
            handler_id='1',
            handler_code='FOO',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='2',
            handler_code='FOO',
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

    assert session.query(Ticket).filter_by(state='archived').count() == 2
    client.delete('/tickets-archive/ALL/delete')
    assert session.query(Ticket).filter_by(state='archived').count() == 0


def test_files_from_ticket_form_submission_are_deleted(client):

    form_submission_collection = FormCollection(client.app.session())
    form_submission_collection.definitions.add(
        'Statistics',
        definition=textwrap.dedent(
            """
            E-Mail * = @@@
            Name * = ___
            Datei * = *.txt
            Datei2 * = *.txt """
        ),
        type='custom',
    )
    transaction.commit()

    client.login_admin()
    page = client.get('/forms').click('Statistics')

    page.form['name'] = 'foobar'
    page.form['e_mail'] = 'foo@bar.ch'
    page.form['datei'] = Upload('README1.txt', b'first')
    page.form['datei2'] = Upload('README2.txt', b'second')

    form_page = page.form.submit().follow()

    assert 'README1.txt' in form_page.text
    assert 'README2.txt' in form_page.text
    assert 'Abschliessen' in form_page.text

    form_page.form.submit()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    ticket_url = ticket_page.request.path
    ticket_page.click('Ticket abschliessen').follow()

    page = client.get('/')

    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '1'

    ticket = client.get(ticket_url)
    ticket.click('Ticket archivieren').follow()

    session = client.app.session()
    files = FileCollection(session).query().all()
    assert len(files) == 2

    # save the handler id for later
    first_ticket = session.query(Ticket).one()
    handler_id = first_ticket.handler.id

    # delete archived, we expect this to also delete the associated files
    client.delete('/tickets-archive/ALL/delete')
    files = FileCollection(session).query().all()
    assert len(files) == 0

    form_submission = FormSubmissionCollection(session).by_id(handler_id)
    assert form_submission is None


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
