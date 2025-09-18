import base64
import json
import re
from textwrap import dedent
from datetime import date, timedelta, datetime

import os

import pytest
import transaction
from freezegun import freeze_time
from webtest import Upload

from onegov.chat import MessageCollection
from onegov.form import FormCollection
from onegov.reservation import ResourceCollection


def get_data_feed_messages(page):
    return json.loads(
        page.pyquery('div.timeline').attr('data-feed-data'))['messages']


def test_tickets(client):

    # feed = ticket_page.pyquery('div.timeline').attr('data-feed-data')
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

    assert len(os.listdir(client.app.maildir)) == 0

    status_page = form_page.form.submit().follow().form.submit().follow()

    assert len(os.listdir(client.app.maildir)) == 1

    message = client.get_email(0)['TextBody']

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

    ticket_page = tickets_page.click('Annehmen').follow()
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    tickets_page = client.get('/tickets/ALL/pending')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '1'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    assert 'editor@example.org' in ticket_page
    assert 'Newsletter' in ticket_page
    assert 'info@seantis.ch' in ticket_page
    assert 'In Bearbeitung' in ticket_page
    assert 'FRM-' in ticket_page
    # ticket timeline
    timeline_messages = get_data_feed_messages(ticket_page)
    assert len(timeline_messages) == 2
    assert 'Ticket eröffnet' in timeline_messages[0]['html']
    assert 'Ticket angenommen' in timeline_messages[1]['html']

    # default is always enable email notifications
    send_msg = ticket_page.request.url + '/message-to-submitter'
    input_field = client.get(send_msg).pyquery('#notify')
    assert input_field.attr('disabled') == 'disabled'

    # Test mail notification on new message
    assert len(os.listdir(client.app.maildir)) == 1
    anon = client.spawn()
    ticket_status = ticket_page.request.url + '/status'
    status = anon.get(ticket_status)
    status.form['text'] = 'Testmessage'
    status.form.submit().follow()

    message = client.get_email(1)

    ticket_url = ticket_page.request.path
    ticket_page = ticket_page.click('Ticket abschliessen').follow()

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '0'
    assert page.pyquery('.closed-tickets').attr('data-count') == '1'

    assert len(os.listdir(client.app.maildir)) == 3

    message = client.get_email(2)['TextBody']

    assert "Ihre Anfrage wurde abgeschlossen" in message
    assert '/status' in message

    assert 'FRM-' in status_page
    assert 'Offen' in status_page

    assert 'Abgeschlossen' in ticket_page
    tickets_page = client.get('/tickets/ALL/closed')

    # the toggle for the deletion of the current subset
    ticket_rows = tickets_page.pyquery('tr.ticket')
    assert len(ticket_rows) == 1
    assert ticket_rows.attr('data-url')

    ticket_page = client.get(ticket_url)
    ticket_page = ticket_page.click('Ticket wieder öffnen').follow()
    # ticket timeline
    timeline_messages = get_data_feed_messages(ticket_page)
    assert len(timeline_messages) == 5
    assert 'Ticket eröffnet.' in timeline_messages[0]['html']
    assert 'Ticket angenommen.' in timeline_messages[1]['html']
    assert 'Testmessage' in timeline_messages[2]['html']
    assert 'Ticket geschlossen.' in timeline_messages[3]['html']
    assert 'Ticket wieder geöffnet.' in timeline_messages[4]['html']

    tickets_page = client.get('/tickets/ALL/pending')
    assert len(tickets_page.pyquery('tr.ticket')) == 1

    page = client.get('/')
    assert page.pyquery('.open-tickets').attr('data-count') == '0'
    assert page.pyquery('.pending-tickets').attr('data-count') == '1'
    assert page.pyquery('.closed-tickets').attr('data-count') == '0'

    message = client.get_email(3)['TextBody']

    assert "Ihre Anfrage wurde wieder " in message
    assert '/status' in message

    # archive the ticket
    client.get(ticket_url).click('Ticket abschliessen').follow()
    ticket = client.get(ticket_url)
    assert 'Löschen' not in ticket
    ticket.click('Ticket archivieren').follow()

    archived_ticket = client.get(ticket_url)
    assert 'Ticket wieder öffnen' not in archived_ticket
    # ticket timeline
    timeline_messages = get_data_feed_messages(archived_ticket)
    assert len(timeline_messages) == 7
    assert 'Ticket archiviert.' in timeline_messages[6]['html']
    archived_ticket = archived_ticket.click('Aus dem Archiv holen').follow()
    assert 'aus dem Archiv geholt' in archived_ticket
    # ticket timeline
    timeline_messages = get_data_feed_messages(archived_ticket)
    assert len(timeline_messages) == 8
    assert 'Ticket aus dem Archiv geholt.' in timeline_messages[7]['html']
    archived_ticket.click('Ticket archivieren').follow()

    # test security
    anon = client.spawn()
    anon.get(ticket_url + '/archive', status=403)


def test_ticket_states_idempotent(client):
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
    page = page.click('Annehmen').follow()
    assert len(os.listdir(client.app.maildir)) == 1
    assert len(client.get('/timeline/feed').json['messages']) == 2

    page.click('Ticket abschliessen')
    page.click('Ticket abschliessen')
    page.click('Ticket abschliessen').follow()
    assert len(os.listdir(client.app.maildir)) == 2
    assert len(client.get('/timeline/feed').json['messages']) == 3

    page = client.get(
        client.get('/tickets/ALL/closed')
        .pyquery('.ticket-number-plain a').attr('href'))

    page.click('Ticket wieder öffnen')
    page.click('Ticket wieder öffnen')
    page = page.click('Ticket wieder öffnen').follow()
    assert len(os.listdir(client.app.maildir)) == 3
    assert len(client.get('/timeline/feed').json['messages']) == 4

    page.click('Ticket abschliessen').follow()
    assert len(os.listdir(client.app.maildir)) == 4
    assert len(client.get('/timeline/feed').json['messages']) == 5

    page = client.get(
        client.get('/tickets/ALL/closed')
        .pyquery('.ticket-number-plain a').attr('href'))

    page.click('Ticket archivieren')
    page = page.click('Ticket archivieren').follow()
    assert len(os.listdir(client.app.maildir)) == 4  # no new mail
    assert len(client.get('/timeline/feed').json['messages']) == 6

    page.click('Aus dem Archiv holen')
    page.click('Aus dem Archiv holen').follow()
    assert len(os.listdir(client.app.maildir)) == 4  # no new mail
    assert len(client.get('/timeline/feed').json['messages']) == 7

    # check timeline messages of ticket
    messages = client.get('/timeline/feed').json['messages']
    expected_messages = [
        'Ticket eröffnet',
        'Ticket angenommen',
        'Ticket geschlossen',
        'Ticket wieder geöffnet',
        'Ticket geschlossen',
        'Ticket archiviert',
        'Ticket aus dem Archiv geholt'
    ]
    for message, expected in zip(messages, expected_messages):
        assert expected in message['html']


def test_ticket_states_directory_entry(client):
    client.login_admin()

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Vereinsverzeichnis"
    page.form['structure'] = "Vereinsname *= ___"
    page.form['title_format'] = "[Vereinsname]"
    page.form['enable_submissions'] = True
    page.form.submit()

    anon = client.spawn()
    page = anon.get('/directories/vereinsverzeichnis').click('Eintrag '
                                                             'vorschlagen')
    page.form['vereinsname'] = 'Minions Fan Club'
    page.form['submitter'] = "bob@minionworld.org"
    page.form.submit().follow().form.submit().follow()

    page = client.get('/tickets/ALL/open')
    page = page.click('Annehmen').follow()

    # reject
    url = page.request.url
    page.click('Eintrag abweisen')

    # withdraw rejection
    client.get(url).click('Ablehnung zurückziehen')

    # accept entry after rejection withdrawal
    client.get(url).click('Übernehmen')

    client.get(url).click('Ticket abschliessen')

    page = client.get(
        client.get('/tickets/ALL/closed')
        .pyquery('.ticket-number-plain a').attr('href'))

    page = page.click('Ticket wieder öffnen').follow()

    page.click('Ticket abschliessen').follow()

    page = client.get(
        client.get('/tickets/ALL/closed')
        .pyquery('.ticket-number-plain a').attr('href'))

    page.click('Ticket archivieren')
    page = page.click('Ticket archivieren').follow()

    page.click('Aus dem Archiv holen').follow()

    # check timeline messages of ticket
    assert len(client.get('/timeline/feed').json['messages']) == 10
    messages = client.get('/timeline/feed').json['messages']
    expected_messages = [
        'Ticket eröffnet',
        'Ticket angenommen',
        'Verzeichniseintrag abgelehnt',
        'Ablehnung des Verzeichniseintrags zurückgezogen',
        'Verzeichniseintrag übernommen',
        'Ticket geschlossen',
        'Ticket wieder geöffnet',
        'Ticket geschlossen',
        'Ticket archiviert',
        'Ticket aus dem Archiv geholt'
    ]

    for message, expected in zip(messages, expected_messages):
        assert expected in message['html']


def test_send_ticket_email(client):
    anon = client.spawn()

    admin = client.spawn()
    admin.login_admin()

    # make sure submitted event emails are sent to everyone, unless the
    # logged-in user is the same as the user responsible for the event
    def submit_event(client, email):
        start = date.today() + timedelta(days=1)

        page = client.get('/events').click("Veranstaltung erfassen")
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

    client.flush_email_queue()

    submit_event(admin, 'admin@example.org')
    assert len(os.listdir(client.app.maildir)) == 0

    submit_event(admin, 'someone-else@example.org')
    assert len(os.listdir(client.app.maildir)) == 1
    assert 'someone-else@example.org' == client.get_email(0)['To']

    submit_event(anon, 'admin@example.org')
    assert len(os.listdir(client.app.maildir)) == 2
    assert 'admin@example.org' == client.get_email(1)['To']

    # ticket notifications can be manually disabled
    page = admin.get('/tickets/ALL/open').click('Annehmen', index=1).follow()
    page = page.click('E-Mails deaktivieren').follow()

    assert 'deaktiviert' in page
    ticket_url = page.request.url
    page = page.click('Ticket abschliessen').follow()

    assert len(os.listdir(client.app.maildir)) == 2
    page = admin.get(ticket_url)
    page = page.click('E-Mails aktivieren').follow()

    page = page.click('Ticket wieder öffnen').follow()
    assert len(os.listdir(client.app.maildir)) == 3

    # make sure the same holds true for forms
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=dedent("""
        Name * = ___
        E-Mail * = @@@
    """), type='custom')
    transaction.commit()

    def submit_form(client, email):
        page = client.get('/forms').click('Profile')
        page.form['name'] = 'foobar'
        page.form['e_mail'] = email
        page.form.submit().follow().form.submit()

    client.flush_email_queue()

    submit_form(admin, 'admin@example.org')
    assert len(os.listdir(client.app.maildir)) == 0

    submit_form(admin, 'someone-else@example.org')
    assert len(os.listdir(client.app.maildir)) == 1
    assert 'someone-else@example.org' == client.get_email(0)['To']

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

    def submit_reservation(client, email, remembered=None):
        assert reserve('10:00', '12:00').json == {'success': True}

        # fill out the form
        formular = client.get('/resource/tageskarte/form')

        # check whether we remembered the previous submission
        if remembered:
            assert formular.form['email'].value == remembered
        formular.form['email'] = email

        formular.form.submit().follow().form.submit().follow()

    client.flush_email_queue()

    submit_reservation(admin, 'admin@example.org')
    assert len(os.listdir(client.app.maildir)) == 0

    submit_reservation(admin, 'someone-else@example.org', 'admin@example.org')
    assert len(os.listdir(client.app.maildir)) == 1
    assert 'someone-else@example.org' == client.get_email(0)['To']


def test_email_for_new_tickets(client):
    client.login_admin()

    # set email adress for new tickets
    settings = client.get('/ticket-settings')
    settings.form['email_for_new_tickets'] = 'new-tickets@test.org'
    settings.form.submit().follow()

    # fill out a form to automatically send a notification mail
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=dedent("""
        Name * = ___
        E-Mail * = @@@
    """), type='custom')
    transaction.commit()

    page = client.get('/forms').click('Profile')
    page.form['name'] = 'foobar'
    page.form['e_mail'] = 'person@example.org'
    page.form.submit().follow().form.submit()

    # same for new events
    start = date.today() + timedelta(days=1)

    page = client.get('/events').click("Veranstaltung erfassen")
    page.form['email'] = "person@example.org"
    page.form['title'] = "My Event"
    page.form['description'] = "My event is an event."
    page.form['organizer'] = "The Organizer"
    page.form['location'] = "A place"
    page.form['start_date'] = start.isoformat()
    page.form['start_time'] = "18:00"
    page.form['end_time'] = "22:00"
    page.form['repeat'] = 'without'

    page.form.submit().follow().form.submit()

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
    reserve = client.bound_reserve(allocations[0])
    transaction.commit()
    assert reserve('10:00', '12:00').json == {'success': True}

    formular = client.get('/resource/tageskarte/form')
    formular.form['email'] = 'person@example.org'
    formular.form.submit().follow().form.submit().follow()

    assert len(os.listdir(client.app.maildir)) == 6
    mails = list()
    for i in range(6):
        mails.append(client.get_email(i))
    mails = sorted(mails, key=lambda d: d['To'])

    assert 'new-tickets@test.org' == mails[0]['To']
    assert 'Das folgende Ticket wurde soeben ' in mails[0]['TextBody']
    assert 'new-tickets@test.org' == mails[1]['To']
    assert 'Das folgende Ticket wurde soeben ' in mails[1]['TextBody']
    assert 'new-tickets@test.org' == mails[2]['To']
    assert 'Das folgende Ticket wurde soeben ' in mails[2]['TextBody']


def test_ticket_notes(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=dedent("""
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
    collection.definitions.add('Profile', definition=dedent("""
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
    assert len(os.listdir(client.app.maildir)) == 1

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
    assert len(os.listdir(client.app.maildir)) == 1

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
    assert len(os.listdir(client.app.maildir)) == 2
    assert "I will correct your name" in client.get_email(1)['TextBody']

    # make sure the reply-to story is good
    mail = client.get_email(1)
    assert mail['To'] == 'foo@bar.baz'
    assert mail['From'] == 'Govikon <mails@govikon.ch>'
    assert mail['ReplyTo'] == 'Govikon <admin@example.org>'

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
    assert len(os.listdir(client.app.maildir)) == 3

    mail = client.get_email(2)['TextBody']
    assert "I will correct your name" in mail
    assert "Great, thanks!" in mail

    # send a final message from the editor, with no notification
    page = client.get(ticket_url).click("Nachricht senden")
    page.form['text'] = "You're welcome"
    page.form.get('notify').checked = False
    page.form.submit()

    # the user always gets a notification
    assert len(os.listdir(client.app.maildir)) == 4

    # but now, the answering wont create one
    page = client.get(status_url)
    page.form['text'] = 'Can I ask you something else?'
    page.form.submit()

    assert len(os.listdir(client.app.maildir)) == 4

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
    assert len(page.forms) == 1

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
    page.form['e_mail'] = 'hans.maulwurf@simpsons.com'
    page = page.form.submit().follow().form.submit().follow()
    ticket_number = page.pyquery('.ticket-number').text()
    assert ticket_number.startswith('FRM-')

    # check visibility
    client.login_editor()
    page = client.get('/tickets/ALL/open')
    assert ticket_number in page
    assert 'hans.maulwurf@simpsons.com' not in page.pyquery(
        '.ticket-group').text()
    assert 'Annehmen' not in page

    client.logout()

    client.login_admin()
    page = client.get('/tickets/ALL/open')
    assert ticket_number in page
    assert 'hans.maulwurf@simpsons.com' in page.pyquery('.ticket-group').text()
    assert 'hans.maulwurf@simpsons.com' in page.click('Annehmen').follow()


def test_assign_tickets(client):
    client.login_admin()

    # add form
    manage = client.get('/forms/new')
    manage.form['title'] = 'newsletter'
    manage.form['definition'] = 'E-Mail *= @@@'
    manage = manage.form.submit()

    client.logout()

    # open a ticket
    page = client.get('/form/newsletter')
    page.form['e_mail'] = 'hans.maulwurf@simpsons.com'
    page = page.form.submit().follow().form.submit().follow()
    ticket_number = page.pyquery('.ticket-number').text()
    assert ticket_number.startswith('FRM-')

    # assign ticket
    client.login_admin()

    manage = client.get('/tickets/ALL/open').click(ticket_number)
    manage = manage.click('E-Mails deaktivieren').follow()
    manage = manage.click('Ticket zuweisen')
    manage.form['user'].select(text='editor@example.org')
    page = manage.form.submit().follow()
    # test timeline
    timeline_messages = get_data_feed_messages(page)
    assert len(timeline_messages) == 3
    assert 'Ticket eröffnet.' in timeline_messages[0]['html']
    assert 'Ticket E-Mails deaktiviert.' in timeline_messages[1]['html']
    assert 'Ticket zugewiesen' in timeline_messages[2]['html']

    client.logout()

    # check visibility
    client.login_editor()

    page = client.get('/').click('Meine Tickets')
    page = page.click(ticket_number)
    assert "Ticket zugewiesen" in page
    assert "(editor@example.org)" in page

    # check mail
    assert len(os.listdir(client.app.maildir)) == 2
    message = client.get_email(1)
    assert message['Subject'] == (
        f'{ticket_number} / newsletter: Sie haben ein neues Ticket'
    )
    assert message['To'] == 'editor@example.org'


def test_bcc_field_in_ticket_message(client):

    client.login_admin()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "Newsletter"
    form_page.form['definition'] = "E-Mail *= @@@"
    form_page.form.submit()

    anon = client.spawn()
    form_page = anon.get('/form/newsletter')
    form_page.form['e_mail'] = 'anonymer-user@example.ch'
    form_page.form.submit().follow().form.submit().follow()

    client.login_admin()
    tickets_page = client.get('/tickets/ALL/open')
    ticket_page = tickets_page.click('Annehmen').follow()
    ticket_url = ticket_page.request.url

    page = client.get(ticket_url).click("Nachricht senden")
    page.form['text'] = "'Bcc' — the photo-bomber of the email world."
    page.form['email_bcc'] = ['editor@example.org']
    page.form.get('notify').checked = True
    page.form.submit()

    client.login_editor()
    message = client.get_email(1)

    assert 'Ihr Ticket hat eine neue Nachricht' in message['Subject']
    assert message['Bcc'] == 'editor@example.org'

    def extract_link(text):
        pattern = r'http://localhost/ticket/FRM/[a-zA-Z0-9]+/status'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    body = message['TextBody']
    assert "'Bcc' — the photo-bomber of the email world." in body
    status_link = extract_link(body)

    status_page = client.get(status_link)
    assert 'fügen Sie der Anfrage eine Nachricht hinzu' in status_page.text

    # test the reply feature now
    msg = 'Hello from the other side, or should I say, Bcc-side?'
    status_page.form['text'] = msg
    status_page.form.submit().follow()

    # the most recent message would be rendered, but requires js.
    # so we go the other way and check the db.
    last_msg = MessageCollection(
        client.app.session(),
        load='newer-first',
        limit=1
    ).query().first()

    assert last_msg.text == msg
    #  Note that if the person in email CC field replies using the link to add
    #  a TicketChatMessage, we have to adjust the owner of the message,
    #  because the message is now actually from that person. Therefore below
    #  assertion has to be False
    assert not last_msg.owner == 'anonymer-user@example.ch'
    assert last_msg.owner == 'editor@example.org'

    # test invalid email
    client.login_admin()
    page.form['text'] = "'Bcc' — the photo-bomber of the email world."
    with pytest.raises(ValueError):
        page.form['email_bcc'] = ['not_an_email']

    return
    # test multiple CC
    # this is not set correctly (Only one email is set), reason unclear
    page.form['email_bcc'].select_multiple(texts=[
        'editor@example.org', 'member@example.org'
    ])
    page.form.get('notify').checked = True
    page.form.submit()

    client.login_editor()
    message = client.get_email(1)
    assert 'Ihr Ticket hat eine neue Nachricht' in message['Subject']
    assert 'editor@example.org' in message['Bcc']
    client.login_member()
    message = client.get_email(1)
    assert 'Ihr Ticket hat eine neue Nachricht' in message['Subject']
    assert 'member@example.org' in message['Bcc']


def test_email_attachment_in_ticket_message(client):

    client.login_admin()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "Newsletter"
    form_page.form['definition'] = "E-Mail *= @@@"
    form_page.form.submit()

    anon = client.spawn()
    form_page = anon.get('/form/newsletter')
    form_page.form['e_mail'] = 'anonymous-user@example.com'
    form_page.form.submit().follow().form.submit().follow()

    client.login_admin()
    tickets_page = client.get('/tickets/ALL/open')
    ticket_page = tickets_page.click('Annehmen').follow()
    ticket_url = ticket_page.request.url

    page = client.get(ticket_url).click("Nachricht senden")
    # create both BCC and attachment
    page.form['text'] = "Attachments make emails heavy."
    page.form['email_bcc'] = ['editor@example.org']
    page.form['email_attachment'] = Upload(
        'Test.txt', b'attached', 'text/plain')
    page.form.submit()

    client.login_editor()
    message = client.get_email(1)

    assert 'Ihr Ticket hat eine neue Nachricht' in message['Subject']

    assert 'editor@example.org' in message['Bcc']
    msg = message['Attachments'][0]
    assert 'Test.txt' in msg.values()
    decoded_content = base64.b64decode(msg['Content'])
    assert decoded_content == b'attached'


def test_hide_personal_mail_in_tickets(client):
    admin = client
    client.login_admin()
    anon = client.spawn()

    page = admin.get('/ticket-settings')
    page.form['hide_personal_email'] = True
    page.form['general_email'] = 'info@organisation.org'
    page.form.submit()

    page = admin.get('/forms/new')
    page.form['title'] = 'Test'
    page.form.submit()

    page = anon.get('/form/test')
    page.form['e_mail'] = 'anon@example.org'
    anon_ticketinfo = page.form.submit().follow().form.submit().follow()

    admin_ticketinfo = admin.get('/tickets/ALL/open').click(
        'Annehmen').follow()
    assert 'admin@example.org' in admin_ticketinfo
    assert 'info@organisation.org' not in admin_ticketinfo

    # Admin sends message
    page = admin_ticketinfo.click('Nachricht senden')
    page.form['text'] = 'Admin message'
    page.form.submit().follow()

    # Anon sends message
    anon_ticketinfo.form['text'] = 'Anon message'
    anon_ticketinfo.form.submit().follow()

    assert len(os.listdir(client.app.maildir)) == 3
    mails = list()
    for i in range(3):
        mails.append(client.get_email(i))
    mails = sorted(mails, key=lambda d: d['To'])

    # Admin sees their own email
    assert 'admin@example' in mails[0]['TextBody']
    assert 'info@organisation' not in mails[0]['TextBody']
    assert 'anon@example' in mails[0]['TextBody']

    # Anon only sees general mail in mail and ticket status
    messsage = mails[1]['TextBody']
    ticket_status = re.search(r'Anfragestatus überprüfen\]\(([^\)]+)',
                              messsage).group(1)
    anon_ticketinfo = anon.get(ticket_status)
    assert 'info@organisation.org' in anon_ticketinfo
    assert 'admin@example.org' not in anon_ticketinfo

    assert 'info@organisation.org' in mails[2]['TextBody']
    assert 'admin@example' not in mails[2]['TextBody']


@freeze_time("2015-08-28", tick=True)
def test_my_tickets_view(client):
    admin = client.spawn()
    admin.login_admin()

    # create a form
    form_page = admin.get('/forms/new')
    form_page.form['title'] = "Newsletter"
    form_page.form['definition'] = "E-Mail *= @@@"
    form_page = form_page.form.submit()

    # create a submission
    form_page = client.get('/form/newsletter')
    form_page.form['e_mail'] = 'info@seantis.ch'
    status_page = form_page.form.submit().follow().form.submit().follow()

    # by default this view is disabled
    client.get('/tickets/ALL/all/my-tickets', status=404)

    # let's enable it
    settings = admin.get('/').click('Einstellungen').click('Kunden-Login')
    settings.form['citizen_login_enabled'].checked = True
    settings.form.submit().follow()

    # now we don't have access yet
    login = client.get('/tickets/ALL/all/my-tickets').follow()
    login.form['email'] = 'info@seantis.ch'
    confirm = login.form.submit().follow()
    assert len(os.listdir(client.app.maildir)) == 2
    message = client.get_email(1)['TextBody']
    token = re.search(r'&token=([^)]+)', message).group(1)
    confirm.form['token'] = token
    tickets = confirm.form.submit().follow()
    assert tickets.request.path_qs == '/tickets/ALL/all/my-tickets'
    assert 'Offen' in tickets
