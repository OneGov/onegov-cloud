import os
import pytz
from onegov.core.utils import normalize_for_url
from onegov.reservation import ResourceCollection
import textwrap
from webtest import Upload
from onegov.file import FileCollection
from onegov.form import FormCollection, FormSubmissionCollection
from onegov.org.models.ticket import FormSubmissionHandler
import transaction
from datetime import datetime
from onegov.core.utils import Bunch
from onegov.ticket import TicketCollection, Ticket
from onegov.user import UserCollection
from sedate import ensure_timezone
from tests.onegov.org.common import register_echo_handler
from tests.shared import Client as BaseClient


class Client(BaseClient):
    skip_n_forms = 1


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
            handler_code='ECH',
            title="Title",
            group="Group",
            email="citizen@example.org",
            created=datetime(2016, 1, 2, 10, tzinfo=tz),
        ),
        collection.open_ticket(
            handler_id='2',
            handler_code='ECH',
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


def test_has_future_reservations(client):
    def setup_resource(
        name, title, definition, dates, whole_day, ctx, client
    ):
        res = ResourceCollection(ctx).by_name(name)
        res.definition, res.title = definition, title
        alloc = res.get_scheduler(ctx).allocate(
            dates=dates, whole_day=whole_day
        )
        return client.bound_reserve(alloc[0])

    def fill_and_submit_form(client, resource_name, form_data):
        formular = client.get(f'/resource/{resource_name}/form')
        for key, value in form_data.items():
            formular.form[key] = value
        formular.form.submit().follow().form.submit()

    def accept_all_reservations(client):
        ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
        ticket.click('Alle Reservationen annehmen')

    ctx = client.app.libres_context
    client.login_admin()

    transaction.begin()
    reserve_daypass = setup_resource(
        'tageskarte',
        'Tageskarte',
        "Vorname *= ___\nNachname *= ___",
        (datetime(2100, 8, 28, 12, 0),
         datetime(2100, 8, 28, 13, 0)),
        False,
        ctx,
        client,
    )

    ResourceCollection(ctx).add(
        "Conference room",
        'Europe/Zurich',
        type='room',
        name='conference-room',
    )

    reserve_room = setup_resource(
        'conference-room',
        normalize_for_url(
            "Gemeindeverwaltung Sitzungszimmer gross (2. OG)"
        ),
        "Name *= ___",
        (datetime(2100, 8, 28),
         datetime(2100, 8, 28)),
        True,
        ctx,
        client,
    )

    transaction.commit()

    assert reserve_daypass().json == {'success': True}
    assert reserve_room().json == {'success': True}

    fill_and_submit_form(
        client,
        'tageskarte',
        {
            'email': 'info@example.org',
            'vorname': 'Charlie',
            'nachname': 'Carson',
        },
    )
    accept_all_reservations(client)

    fill_and_submit_form(client, 'conference-room', {'name': 'Name'})
    accept_all_reservations(client)

    session = client.app.session()
    handlers = [h.handler for h in session.query(Ticket)]
    assert all(h.has_future_reservation for h in handlers)

    # now setup a reservation which is in the past
    transaction.begin()

    ResourceCollection(ctx).add(
        "Conference room",
        'Europe/Zurich',
        type='room',
        name='conference-room2',
    )
    reserve_room2 = setup_resource(
        'conference-room2',
        'Conference Room',
        "Vorname *= ___\nNachname *= ___",
        (datetime(2009, 8, 28, 12, 0),
         datetime(2009, 8, 28, 13, 0)),
        False,
        ctx,
        client,
    )
    transaction.commit()

    assert reserve_room2().json == {'success': True}

    fill_and_submit_form(
        client,
        'conference-room2',
        {
            'email': 'info2@example.org',
            'vorname': 'Charlie2',
            'nachname': 'Carson2',
        },
    )

    accept_all_reservations(client)

    session = client.app.session()
    handler = [
        t.handler
        for t in session.query(Ticket).filter(
            Ticket.title == '28.08.2009 12:00 - 13:00'
        )
    ][0]
    assert not handler.has_future_reservation


def test_most_future_reservation(client):
    client.login_admin()

    transaction.begin()

    resource = client.app.libres_resources.by_name('tageskarte')
    thursday = resource.scheduler.allocate(
        dates=(datetime(2016, 4, 28), datetime(2016, 4, 28)),
        whole_day=True
    )[0]
    friday = resource.scheduler.allocate(
        dates=(datetime(2024, 4, 29), datetime(2024, 4, 29)),
        whole_day=True
    )[0]

    reserve_thursday = client.bound_reserve(thursday)
    reserve_friday = client.bound_reserve(friday)
    transaction.commit()

    reserve_thursday()
    reserve_friday()
    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = "info@example.org"
    confirmation = formular.form.submit().follow()
    confirmation.form.submit().follow()
    ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()

    # accept it
    ticket.click('Alle Reservationen annehmen')

    query = client.app.session().query(Ticket)
    assert query.count() == 1
    # 1 ticket with multiple allocations
    ticket = query.one()
    assert ticket.handler.most_future_reservation.start == datetime(
        2024, 4, 28, 22, 0, tzinfo=pytz.utc
    )
