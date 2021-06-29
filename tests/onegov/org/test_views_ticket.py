import json
import re
import textwrap
from datetime import date, timedelta, datetime

import transaction
from webtest import Upload

from onegov.form import FormCollection
from onegov.reservation import ResourceCollection
from tests.onegov.org.common import get_mail


def test_tickets(client):

    assert client.get(
        '/tickets/ALL/open', expect_errors=True).status_code == 403

    assert len(client.get('/').pyquery(
        '.open-tickets, .pending-tickets, .closed-tickets'
    )) == 0

    client.login_editor()

    page = client.get('/')
    assert len(page.pyquery(
        '.open-tickets, .pending-tickets, .closed-tickets'
    )) == 3

    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    form_page = client.get('/forms/new')
    form_page.form['title'] = "Newsletter"
    form_page.form['definition'] = "E-Mail *= @@@"
    form_page = form_page.form.submit()

    client.logout()

    form_page = client.get('/form/newsletter')
    form_page.form['e_mail'] = 'info@seantis.ch'

    assert len(client.app.smtp.outbox) == 0

    status_page = form_page.form.submit().follow().form.submit().follow()

    assert len(client.app.smtp.outbox) == 1

    message = client.app.smtp.outbox[0]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert 'FRM-' in message
    assert '/status' in message

    assert 'FRM-' in status_page
    assert 'Offen' in status_page

    client.login_editor()

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '1'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    tickets_page = client.get('/tickets/ALL/open')
    assert len(tickets_page.pyquery('tr.ticket')) == 1
    assert not tickets_page.pyquery('a.ticket-filter-deletable')

    ticket_page = tickets_page.click('Annehmen').follow()
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    tickets_page = client.get('/tickets/ALL/pending')
    assert len(tickets_page.pyquery('tr.ticket')) == 1
    assert not tickets_page.pyquery('a.ticket-filter-deletable')

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '1'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    assert 'editor@example.org' in ticket_page
    assert 'Newsletter' in ticket_page
    assert 'info@seantis.ch' in ticket_page
    assert 'In Bearbeitung' in ticket_page
    assert 'FRM-' in ticket_page

    # default is always enable email notifications
    send_msg = ticket_page.request.url + '/message-to-submitter'
    input_field = client.get(send_msg).pyquery('#notify')
    assert input_field.attr('disabled') == 'disabled'

    # Test mail notification on new message
    assert len(client.app.smtp.outbox) == 1
    anon = client.spawn()
    ticket_status = ticket_page.request.url + '/status'
    status = anon.get(ticket_status)
    status.form['text'] = 'Testmessage'
    status.form.submit().follow()

    message = get_mail(client.app.smtp.outbox, 1)

    ticket_url = ticket_page.request.path
    ticket_page = ticket_page.click('Ticket abschliessen').follow()

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '1'

    assert len(client.app.smtp.outbox) == 3

    message = client.app.smtp.outbox[2]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert "Ihre Anfrage wurde abgeschlossen" in message
    assert '/status' in message

    assert 'FRM-' in status_page
    assert 'Offen' in status_page

    assert 'Abgeschlossen' in ticket_page
    tickets_page = client.get('/tickets/ALL/closed')

    # the toggle for the deletion of the current subset
    assert tickets_page.pyquery('a.ticket-filter-deletable')
    ticket_rows = tickets_page.pyquery('tr.ticket')
    assert len(ticket_rows) == 1
    assert ticket_rows.attr('data-url')

    # check subset of ticket which is still decided since it has no
    # registration window
    deleting = tickets_page.click('Löschbar')
    assert deleting.pyquery('tr.ticket')

    ticket_page = client.get(ticket_url)
    assert ticket_page.pyquery('.ticket-button.ticket-delete')
    ticket_page = ticket_page.click('Ticket wieder öffnen').follow()

    tickets_page = client.get('/tickets/ALL/pending')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '1'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    message = client.app.smtp.outbox[3]
    message = message.get_payload(0).get_payload(decode=True)
    message = message.decode('iso-8859-1')

    assert "Ihre Anfrage wurde wieder " in message
    assert '/status' in message

    # delete the ticket
    client.get(ticket_url).click('Ticket abschliessen').follow()
    client.get(ticket_url).click('Löschen')


def test_ticket_states_idempotent(client):
    client.login_editor()

    page = client.get('/forms/new')
    page.form['title'] = "Newsletter"
    page.form['definition'] = "E-Mail *= @@@"
    page = page.form.submit()

    page = client.get('/form/newsletter')
    page.form['e_mail'] = 'info@seantis.ch'

    page.form.submit().follow().form.submit().follow()
    assert len(client.app.smtp.outbox) == 1
    assert len(client.get('/timeline/feed').json['messages']) == 1

    page = client.get('/tickets/ALL/open')
    page.click('Annehmen')
    page.click('Annehmen')
    page = page.click('Annehmen').follow()
    assert len(client.app.smtp.outbox) == 1
    assert len(client.get('/timeline/feed').json['messages']) == 2

    page.click('Ticket abschliessen')
    page.click('Ticket abschliessen')
    page = page.click('Ticket abschliessen').follow()
    assert len(client.app.smtp.outbox) == 2
    assert len(client.get('/timeline/feed').json['messages']) == 3

    page = client.get(
        client.get('/tickets/ALL/closed')
        .pyquery('.ticket-number-plain a').attr('href'))

    page.click('Ticket wieder öffnen')
    page.click('Ticket wieder öffnen')
    page = page.click('Ticket wieder öffnen').follow()
    assert len(client.app.smtp.outbox) == 3
    assert len(client.get('/timeline/feed').json['messages']) == 4


def test_send_ticket_email(client):
    anon = client.spawn()

    admin = client.spawn()
    admin.login_admin()

    # make sure submitted event emails are sent to everyone, unless the
    # logged-in user is the same as the user responsible for the event
    def submit_event(client, email):
        start = date.today() + timedelta(days=1)

        page = client.get('/events').click("Veranstaltung melden")
        page.form['email'] = email
        page.form['title'] = "My Event"
        page.form['description'] = "My event is an event."
        page.form['organizer'] = "The Organizer"
        page.form['location'] = "A place"
        page.form['start_date'] = start.isoformat()
        page.form['start_time'] = "18:00"
        page.form['end_time'] = "22:00"
        page.form['repeat'] = 'without'

        page.form.submit().follow().form.submit()

    del client.app.smtp.outbox[:]

    submit_event(admin, 'admin@example.org')
    assert len(client.app.smtp.outbox) == 0

    submit_event(admin, 'someone-else@example.org')
    assert len(client.app.smtp.outbox) == 1
    assert 'someone-else@example.org' == client.app.smtp.outbox[0]['To']

    submit_event(anon, 'admin@example.org')
    assert len(client.app.smtp.outbox) == 2
    assert 'admin@example.org' == client.app.smtp.outbox[1]['To']

    # ticket notifications can be manually disabled
    page = admin.get('/tickets/ALL/open').click('Annehmen', index=1).follow()
    page = page.click('E-Mails deaktivieren').follow()

    assert 'deaktiviert' in page
    ticket_url = page.request.url
    page = page.click('Ticket abschliessen').follow()

    assert len(client.app.smtp.outbox) == 2
    page = admin.get(ticket_url)
    page = page.click('E-Mails aktivieren').follow()

    page = page.click('Ticket wieder öffnen').follow()
    assert len(client.app.smtp.outbox) == 3

    # make sure the same holds true for forms
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        Name * = ___
        E-Mail * = @@@
    """), type='custom')
    transaction.commit()

    def submit_form(client, email):
        page = client.get('/forms').click('Profile')
        page.form['name'] = 'foobar'
        page.form['e_mail'] = email
        page.form.submit().follow().form.submit()

    del client.app.smtp.outbox[:]

    submit_form(admin, 'admin@example.org')
    assert len(client.app.smtp.outbox) == 0

    submit_form(admin, 'someone-else@example.org')
    assert len(client.app.smtp.outbox) == 1
    assert 'someone-else@example.org' == client.app.smtp.outbox[0]['To']

    # and for reservations
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    scheduler = resource.get_scheduler(client.app.libres_context)

    allocations = scheduler.allocate(
        dates=(datetime(2015, 8, 28, 10), datetime(2015, 8, 28, 14)),
        whole_day=False,
        partly_available=True,
        quota=10
    )

    reserve = admin.bound_reserve(allocations[0])
    transaction.commit()

    def submit_reservation(client, email):
        assert reserve('10:00', '12:00').json == {'success': True}

        # fill out the form
        formular = client.get('/resource/tageskarte/form')
        formular.form['email'] = email

        formular.form.submit().follow().form.submit().follow()

    del client.app.smtp.outbox[:]

    submit_reservation(admin, 'admin@example.org')
    assert len(client.app.smtp.outbox) == 0

    submit_reservation(admin, 'someone-else@example.org')
    assert len(client.app.smtp.outbox) == 1
    assert 'someone-else@example.org' == client.app.smtp.outbox[0]['To']


def test_ticket_notes(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        First name * = ___
        Last name * = ___
        E-Mail * = @@@
    """), type='custom')

    transaction.commit()

    # submit a form
    client.login_admin()

    page = client.get('/forms').click('Profile')
    page.form['first_name'] = 'Foo'
    page.form['last_name'] = 'Bar'
    page.form['e_mail'] = 'foo@bar.baz'
    page = page.form.submit().follow().form.submit().follow()

    # make sure a ticket has been created
    assert 'FRM-' in page
    assert 'ticket-state-open' in page

    # add a note
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    page = page.click("Neue Notiz")
    page.form['text'] = "Looks like example input to me"
    page = page.form.submit().follow()

    assert "Looks like example input to me" in page

    # make sure we have a badge with the number of notes
    assert page.pyquery('.counts-note .counts-value').text() == '1'

    # edit the note
    note_url_ex = re.compile(r'http://localhost/ticket-notes/[A-Z0-9]+')
    note_url = note_url_ex.search(str(page)).group()

    page = client.get(note_url + '/edit')
    page.form['text'] = "I will investigate"
    page = page.form.submit().follow()

    assert "I will investigate" in page

    # delete the note
    csrf_token_ex = re.compile(r'\?csrf-token=[a-zA-Z0-9\._\-]+')
    csrf_token = csrf_token_ex.search(str(page)).group()

    client.delete(note_url + csrf_token)
    page = client.get(page.request.url)

    assert "I will investigate" not in page

    # upload a file
    page = page.click("Neue Notiz")
    page.form['text'] = "The profile is actually okay, I got an ID scan"
    page.form['file'] = Upload('Test.txt', b'Proof')
    page = page.form.submit().follow()

    assert "The profile is actually okay" in page
    assert "Test.txt" in page

    # access the file
    file_url_ex = re.compile(r'http://localhost/storage/[A-Z0-9a-z]+')
    file_url = file_url_ex.search(str(page)).group()

    page = client.get(file_url)
    assert page.body == b"Proof"

    # anonymous users do not have access to these files
    assert page.cache_control.private
    assert client.spawn().get(file_url, expect_errors=True).status_code == 404

    # make sure we see it in the timeline as well
    page = client.get('/timeline')
    assert "The profile is actually okay" in page
    assert "Test.txt" in page


def test_ticket_chat(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        First name * = ___
        Last name * = ___
        E-Mail * = @@@
    """), type='custom')
    client.app.org.ticket_always_notify = False
    transaction.commit()

    # submit a form
    client.login_admin()

    page = client.get('/forms').click('Profile')
    page.form['first_name'] = 'Foo'
    page.form['last_name'] = 'Bar'
    page.form['e_mail'] = 'foo@bar.baz'
    page = page.form.submit().follow().form.submit().follow()

    # make sure a ticket has been created
    assert 'FRM-' in page
    assert 'ticket-state-open' in page

    # to extract the messages from the page
    def extract_messages(page):
        text = page.pyquery('[data-feed-data]').attr('data-feed-data')
        data = json.loads(text)

        return data['messages']

    # we should see the initial ticket state in the messages
    msgs = extract_messages(page)
    assert len(msgs) == 1
    assert "Ticket eröffnet" in msgs[0]['html']

    # we should also see one e-mail at this point
    assert len(client.app.smtp.outbox) == 1

    # at this point we have the option to send an initial message
    page.form['text'] = "I spelt my name wrong: it's Baz, not Bar"
    page = page.form.submit().follow()

    # which should show up in the status page and the ticket page
    status_url = page.request.url

    msgs = extract_messages(page)
    assert len(msgs) == 2
    assert "I spelt my name wrong" in msgs[1]['html']

    # we should see the same infos on the ticket page
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    msgs = extract_messages(page)
    assert len(msgs) == 3
    assert "I spelt my name wrong" in msgs[1]['html']
    assert "Ticket angenommen" in msgs[2]['html']

    assert page.pyquery('.counts-external .counts-value').text() == '1'

    # no e-mail will have been created for this message, as there's no
    # recipient we could send it to
    assert len(client.app.smtp.outbox) == 1

    # add a note and let's ensure that the status page does not contain it
    page = page.click("Neue Notiz")
    page.form['text'] = "Contacting the user"
    page = page.form.submit().follow()

    msgs = extract_messages(page)
    assert len(msgs) == 4
    assert "Contacting the user" in msgs[3]['html']

    msgs = extract_messages(client.get(status_url))
    assert len(msgs) == 3
    assert "Contacting the user" not in json.dumps(msgs)

    # answer the user, enable notifications to the editor
    ticket_url = page.request.url

    page = page.click("Nachricht senden")
    page.form['text'] = "I will correct your name"
    page.form.get('notify').checked = True
    page.form.submit()

    # ensure the user sees the message on the status page
    msgs = extract_messages(client.get(status_url))

    assert len(msgs) == 4
    assert "I will correct your name" in msgs[-1]['html']

    # ensure the user sees the message in an e-mail
    assert len(client.app.smtp.outbox) == 2
    assert "I will correct your name" in client.get_email(1)

    # make sure the reply-to story is good
    mail = client.app.smtp.outbox[1]
    assert mail['To'] == 'foo@bar.baz'
    assert mail['From'] == 'Govikon <mails@govikon.ch>'
    assert mail['Reply-To'] == 'Govikon <admin@example.org>'

    # ensure the editor sees the messages in the ticket view
    msgs = extract_messages(client.get(ticket_url))

    assert len(msgs) == 5
    assert "I will correct your name" in msgs[-1]['html']

    page = client.get(ticket_url)
    assert page.pyquery('.counts-internal .counts-value').text() == '1'

    # answer the editor
    page = client.get(status_url)
    page.form['text'] = 'Great, thanks!'
    page.form.submit()

    # the editor should get a notification with the last message
    assert len(client.app.smtp.outbox) == 3

    mail = client.get_email(2)
    assert "I will correct your name" in mail
    assert "Great, thanks!" in mail

    # send a final message from the editor, with no notification
    page = client.get(ticket_url).click("Nachricht senden")
    page.form['text'] = "You're welcome"
    page.form.get('notify').checked = False
    page.form.submit()

    # the user always gets a notification
    assert len(client.app.smtp.outbox) == 4

    # but now, the answering wont create one
    page = client.get(status_url)
    page.form['text'] = 'Can I ask you something else?'
    page.form.submit()

    assert len(client.app.smtp.outbox) == 4

    # though it will still show up in the list
    msgs = extract_messages(client.get(ticket_url))

    assert len(msgs) == 8
    assert "Can I ask you something else?" in msgs[-1]['html']

    # close the ticket
    status_before = client.get(status_url)
    assert "Ticket wurde bereits geschlossen" not in status_before

    page = client.get(ticket_url)
    page.click("Ticket abschliessen")

    # we should no longer be able to send messages
    page = client.get(status_url)
    len(page.forms) == 1

    status_before.form['text'] = 'Foo'
    page = status_before.form.submit()

    assert "Ticket wurde bereits geschlossen" in page

    # verify the same for the editor
    page = client.get(ticket_url)
    assert "Zu geschlossenen Tickets können keine Nachrichten" in page

    page = client.get(ticket_url + '/message-to-submitter')
    page.form['text'] = 'One more thing'
    page = page.form.submit()

    assert "Ticket wurde bereits geschlossen" in page


def test_disable_tickets(client):
    client.login_admin()

    # add form
    manage = client.get('/forms/new')
    manage.form['title'] = 'newsletter'
    manage.form['definition'] = 'E-Mail *= @@@'
    manage = manage.form.submit()

    # add user group
    manage = client.get('/usergroups/new')
    manage.form['name'] = 'Group'
    manage.form['users'].select_multiple(texts=['admin@example.org'])
    manage.form['ticket_permissions'].select_multiple(texts=['FRM'])
    manage = manage.form.submit()

    client.logout()

    # open a ticket
    page = client.get('/form/newsletter')
    page.form['e_mail'] = 'hans.maulwurf@simpson.com'
    page = page.form.submit().follow().form.submit().follow()
    ticket_number = page.pyquery('.ticket-number').text()
    assert ticket_number.startswith('FRM-')

    # check visibility
    client.login_editor()
    page = client.get('/tickets/ALL/open')
    assert ticket_number in page
    assert 'hans.maulwurf@simpson.com' not in page
    assert 'Annehmen' not in page

    client.logout()

    client.login_admin()
    page = client.get('/tickets/ALL/open')
    assert ticket_number in page
    assert 'hans.maulwurf@simpson.com' in page
    assert 'hans.maulwurf@simpson.com' in page.click('Annehmen').follow()
