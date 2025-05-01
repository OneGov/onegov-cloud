import textwrap
from itertools import chain, repeat
from datetime import date

from onegov.file import FileCollection
from onegov.form import FormCollection
from onegov.org.models import TicketNote
from onegov.ticket import Ticket
from onegov.user import UserCollection
from tests.onegov.town6.common import step_class
import transaction
import zipfile
from webtest import Upload
from io import BytesIO
from freezegun import freeze_time
from collections import namedtuple
from unittest.mock import patch


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.authenticate')
@patch('onegov.websockets.integration.broadcast')
def test_form_steps(broadcast, authenticate, connect, client):
    page = client.get('/form/familienausweis')
    assert step_class(page, 1) == 'is-current'

    for name in ('ehefrau', 'ehemann'):
        page.form[f'personalien_{name}_vorname'] = 'L'
        page.form[f'personalien_{name}_name'] = 'L'
        page.form[f'personalien_{name}_ledigname'] = 'L'
        page.form[f'personalien_{name}_geburtsdatum'] = '2020-01-01'
        page.form[f'personalien_{name}_heimatort'] = '2020-01-01'

    page.form['eheschliessung_plz_ort_eheschliessung'] = 'Z'
    page.form['eheschliessung_datum_eheschliessung'] = '2020-01-01'
    page.form['versand_versand_strasse_inkl_hausnummer_'] = '2020-01-01'
    page.form['versand_versand_plz_ort'] = 'U'
    page.form['kontakt_bemerkungen_telefon'] = '044 444 44 44'
    page.form['kontakt_bemerkungen_e_mail'] = 'z@z.ch'

    page = page.form.submit().follow()
    assert step_class(page, 1) == 'is-complete'
    assert step_class(page, 2) == 'is-current'
    assert step_class(page, 3) == ''

    page = page.form.submit().follow()
    assert step_class(page, 1) == 'is-complete'
    assert step_class(page, 2) == 'is-complete'
    assert step_class(page, 3) == 'is-current'

    msg = client.get_email(-1)['TextBody']
    assert 'Ihre Anfrage wurde unter der folgenden Referenz registriert' in msg

    assert connect.call_count == 1
    assert authenticate.call_count == 1
    assert broadcast.call_count == 1
    assert broadcast.call_args[0][3]['event'] == 'browser-notification'
    assert broadcast.call_args[0][3]['title'] == 'Neues Ticket'
    assert broadcast.call_args[0][3]['created']


def test_registration_ticket_workflow(client):
    collection = FormCollection(client.app.session())
    users = UserCollection(client.app.session())

    form = collection.definitions.add('Meetup', textwrap.dedent("""
        E-Mail *= @@@
        Name *= ___
    """), 'custom')

    form.add_registration_window(
        start=date(2018, 1, 1),
        end=date(2018, 1, 31),
        limit=10,
        overflow=False
    )
    username = 'automaton@example.org'
    user_id = users.add(username, 'testing', 'admin').id
    transaction.commit()

    count = 0

    def register(
        client, data_in_email,
        accept_ticket=True, url='/form/meetup'
    ):
        nonlocal count
        count += 1
        with freeze_time(f'2018-01-01 00:00:{count:02d}'):
            page = client.get(url)
            page.form['e_mail'] = f'info{count}@example.org'
            page.form['name'] = 'Foobar'
            page = page.form.submit().follow()

            page.form['send_by_email'] = data_in_email
            page = page.form.submit().follow()
        if not accept_ticket:
            return page
        return client.get('/tickets/ALL/open').click("Annehmen").follow()

    client.login_editor()

    # user info1
    page = register(client, data_in_email=True)

    assert "bestätigen" in page
    assert "ablehnen" in page

    msg = client.get_email(-1)['TextBody']
    assert "Ihre Anfrage wurde unter der folgenden Referenz registriert" in msg
    assert "Foobar" in msg

    page = page.click("Anmeldung bestätigen").follow()

    msg = client.get_email(-1)['TextBody']
    assert 'Ihre Anmeldung für "Meetup" wurde bestätigt' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" in msg

    page.click("Anmeldung stornieren").follow()

    msg = client.get_email(-1)['TextBody']
    assert 'Ihre Anmeldung für "Meetup" wurde storniert' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" in msg

    # user info2
    page = register(client, data_in_email=False)

    msg = client.get_email(-1)['TextBody']
    assert "Ihre Anfrage wurde unter der folgenden Referenz registriert" in msg
    assert "Foobar" not in msg

    page.click("Anmeldung ablehnen")

    msg = client.get_email(-1)['TextBody']
    assert 'Ihre Anmeldung für "Meetup" wurde abgelehnt' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" not in msg

    # create one undecided submission
    register(client, False, accept_ticket=False)

    # Test auto accept reservations for forms
    # views in order:
    # - /form/meetup
    # - /form-preview/{id} mit submit convert Pending in CompleteFormSubmission
    # confirm link: request.link(self.submission, 'confirm-registration')

    client.login_admin()
    settings = client.get('/ticket-settings')
    # skip_opening_email has not effect for the auto-accept setting
    # this opening mail is never sent, instead the confirmation directly
    settings.form['ticket_auto_accepts'] = ['FRM']
    settings.form['auto_closing_user'] = username
    settings.form.submit().follow()

    client = client.spawn()
    page = register(client, False, accept_ticket=False)
    email = client.get_email(-1)
    assert 'Meetup: Ihre Anmeldung wurde bestätigt' in email['Subject']
    assert 'Ihr Anliegen wurde abgeschlossen' in page

    # check ownership of the ticket
    client.app.session().query(Ticket).filter_by(user_id=user_id).one()

    client.login_editor()
    # We rename the form and check if everything still works
    rename_page = client.get('/form/meetup').click('URL ändern')
    assert rename_page.form['name'].value == 'meetup'

    rename_page = rename_page.form.submit()
    assert 'Bitte geben sie einen neuen Namen an' in rename_page

    rename_page.form['name'] = 'ME'
    rename_page = rename_page.form.submit()
    assert 'Ungültiger Name. Ein gültiger Vorschlag ist' in rename_page

    rename_page.form['name'] = 'meetings'
    rename_page = rename_page.form.submit().follow()
    new_url = rename_page.request.url
    assert 'meetings' in new_url

    # Reopen the last
    page = client.get('/tickets/ALL/closed')
    last_ticket = page.pyquery('td.ticket-number-plain a').attr('href')
    ticket = client.get(last_ticket).click('Ticket wieder öffnen').follow()
    window = ticket.click('Anmeldezeitraum')
    assert 'Offen (1)' in window
    assert 'Bestätigt (1)' in window
    assert 'Storniert (2)' in window

    message = window.click('E-Mail an Teilnehmende')
    message.form['message'] = 'Message for all the attendees'
    message.form['registration_state'] = ['open', 'cancelled', 'confirmed']
    page = message.form.submit().follow()
    assert 'Erfolgreich 4 E-Mails gesendet' in page

    latest_ticket_note = (
        client.app.session().query(TicketNote)
        .order_by(TicketNote.created.desc())
        .first()
    )
    assert "Neue E-Mail" in latest_ticket_note.text

    mail = client.get_email(-1)
    assert 'Message for all the attendees' in mail['HtmlBody']
    assert 'Allgemeine Nachricht' in mail['Subject']

    # navigate to the registration window an cancel all
    window.click('Anmeldezeitraum absagen')
    assert 'Storniert (4)' in client.get(window.request.url)

    # Try deleting the form with active registrations window
    form_page = client.get('/form/meetings')
    assert 'Dies kann nicht rückgängig gemacht werden.' in \
           form_page.pyquery('.delete-link.confirm').attr('data-confirm-extra')

    form_delete_link = form_page.pyquery(
        '.delete-link.confirm').attr('ic-delete-from')

    client.delete(form_delete_link, status=200)


def test_form_group_sort(client):
    client.login_editor()

    groups = ['Aaaantelope', 'Allgemein', 'Apple', 'Zzzebra']

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Form"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['group'] = "Zzzebra"
    form_page.form['definition'] = "E-Mail * = @@@"
    form_page = form_page.form.submit()

    form_page = client.get('/forms/new')
    form_page.form['title'] = "My Formiorm"
    form_page.form['lead'] = "This is a form"
    form_page.form['text'] = "There are many like it, but this one's mine"
    form_page.form['group'] = "Apple"
    form_page.form['definition'] = "E-Mail * = @@@"
    form_page = form_page.form.submit()

    form_page = client.get('/external-links/new')
    form_page.form['title'] = "My Formius"
    form_page.form['lead'] = "This is a form"
    form_page.form['url'] = "https://example.ch"
    form_page.form['group'] = "Apple"
    form_page = form_page.form.submit()

    form_page = client.get('/external-links/new')
    form_page.form['title'] = "My Formeros"
    form_page.form['lead'] = "This is a form"
    form_page.form['url'] = "https://example.ch"
    form_page.form['group'] = "Aaaantelope"
    form_page = form_page.form.submit()

    page = client.get('/forms')

    assert groups == page.pyquery(
        '.page-content-main h2').text().strip().split(' ')


def test_forms_without_group_are_displayed(client, forms):

    Form = namedtuple('Form', ['name', 'title', 'definition'])
    forms = [Form(*t) for t in forms]

    groups = {
        'Abstimmungen und Wahlen': 2,
        'Einwohnerkontrolle': 2,
        'Finanzen / Steuern': 1,
        '': 2,  # if no group, the default group "General" is set
        'Friedhof / Bestattungen': 3,
        'Gemeindeammannamt': 1,
        'Jugend / Sport / Vereine': 1,
        'Kommunikation': 2,
        'Planung / Bau': 1,
        'Shop': 1,
        'Soziales / Gesundheit': 2,
        'Umwelt / Energie / Sicherheit': 1,
    }
    total = sum(value for value in groups.values())
    # the numbers above are random, but make sure the sum is the total length:
    assert total == len(forms)

    def expand_groups_i_times(_groups):
        """ Returns list that repeats each key the desired amount of times"""
        return list(chain.from_iterable(
            repeat(key, i) for key, i in _groups.items())
        )

    group_stream = expand_groups_i_times(groups)

    client.login_admin()
    for form, group in zip(forms, group_stream):
        form_page = client.get(f"/form/{form.name}/edit")
        if group:
            form_page.form['group'] = group
            form_page.form.submit()

    form_page = client.get('/forms')
    titles = [form.title for form in forms]
    for t in titles:
        assert t in form_page

    custom_form_title = "Explicit General Group"
    form_page = client.get('/forms/new')
    form_page.form['title'] = custom_form_title
    form_page.form['definition'] = "E-Mail * = @@@"
    form_page.form['group'] = "Allgemein"
    form_page.form.submit()
    form_page = client.get('/forms')
    # Before ogc-857, forms in "General" group have been overwritten
    titles += custom_form_title
    for t in titles:
        assert t in form_page


def test_navbar_links_visibility(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        First name * = ___
        Last name * = ___
        E-Mail * = @@@
    """), type='custom')

    transaction.commit()

    client.login_admin()

    page = client.get("/forms").click("Profile")
    page.form["first_name"] = "Foo"
    page.form["last_name"] = "Bar"
    page.form["e_mail"] = "admin@example.org"
    page = page.form.submit().follow().form.submit().follow()
    ticket_number = page.pyquery(".ticket-number").text()
    page = client.get("/tickets/ALL/open").click(ticket_number)
    # the Gever upload button should not be shown ...
    assert "Hochladen auf Gever" not in page

    settings = client.get('/settings').click('Gever API')
    settings.form['gever_username'] = 'foo'
    settings.form['gever_password'] = 'bar'
    settings.form['gever_endpoint'] = 'https://example.org/'
    settings.form.submit()

    page = client.get("/tickets/ALL/open").click(ticket_number)
    # ... until it has been activated in settings
    assert "Hochladen auf Gever" in page


def test_file_export_for_ticket(client, temporary_directory):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Statistics', definition=textwrap.dedent("""
        E-Mail * = @@@
        Name * = ___
        Datei * = *.txt
        Datei2 * = *.txt """), type='custom')
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

    assert 'Dateien herunterladen' in ticket_page.text
    file_response = ticket_page.click('Dateien herunterladen')

    assert file_response.content_type == 'application/zip'

    with zipfile.ZipFile(BytesIO(file_response.body), 'r') as zip_file:
        zip_file.extractall(temporary_directory)
        file_names = sorted(zip_file.namelist())

        assert {'README1.txt', 'README2.txt'}.issubset(file_names)

        for file_name, content in zip(file_names, [b'first', b'second']):
            with zip_file.open(file_name) as file:
                extracted_file_content = file.read()
                assert extracted_file_content == content

    # test one where the file got deleted
    page.form['name'] = 'foobar'
    page.form['e_mail'] = 'foo@bar.ch'
    page.form['datei'] = Upload('README3.txt', b'third')
    page.form['datei2'] = Upload('README4.txt', b'fourth')

    form_page = page.form.submit().follow()

    assert 'README3.txt' in form_page.text
    assert 'README4.txt' in form_page.text
    assert 'Abschliessen' in form_page.text

    form_page.form.submit()

    files = FileCollection(client.app.session())
    file = files.by_filename('README3.txt').one()
    client.app.session().delete(file)
    client.app.session().flush()

    ticket_page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    # the deleted file is not in the zip
    file_response = ticket_page.click('Dateien herunterladen')

    assert file_response.content_type == 'application/zip'

    with zipfile.ZipFile(BytesIO(file_response.body), 'r') as zip_file:
        zip_file.extractall(temporary_directory)
        file_names = sorted(zip_file.namelist())

        assert 'README3.txt' not in file_names

        for file_name, content in zip(file_names, [b'fourth']):
            with zip_file.open(file_name) as file:
                extracted_file_content = file.read()
                assert extracted_file_content == content


def test_save_and_cancel_in_editbar(client):
    client.login_admin()
    page = client.get('/editor/edit/page/1')
    assert 'save-link' in page
    assert 'cancel-link' in page

    page = client.get('/editor/new/page/1')
    assert 'save-link' in page
    assert 'cancel-link' in page

    page = client.get('/forms/new')
    assert 'save-link' in page
    assert 'cancel-link' in page

    page = client.get('/directories/+new')
    assert 'save-link' in page
    assert 'cancel-link' in page

    page = client.get('/events/enter-event')
    assert 'save-link' in page
    assert 'cancel-link' in page


def test_copy_event(client):
    with freeze_time('2025-04-28 08:00:00'):
        client.login_admin()

        page = client.get('/events/enter-event')
        page.form['email'] = 'art@club.org'
        page.form['title'] = 'Painting Cats'
        page.form['start_date'] = date(2025, 4, 28).isoformat()
        page.form['start_time'] = "18:00"
        page.form['end_time'] = "22:00"
        page.form['location'] = 'Art Gallery'
        page.form['organizer'] = 'Art Club'
        page.form['repeat'] = 'without'

        page = page.form.submit().follow().follow()
        page = page.click('Painting Cats')
        assert 'Painting Cats' in page
        assert 'Montag, 28. April 2025' in page
        assert '18:00 - 22:00' in page
        assert 'Art Gallery' in page
        assert 'Art Club' in page

        page = page.click('Kopieren')
        assert 'Veranstaltung hinzufügen' in page
        page.form['title'] = 'Painting Dogs'
        page = page.form.submit().follow().follow()
        assert 'erfolgreich erstellt' in page

        assert 'Painting Dogs' in page
        assert 'Painting Cats' in page

        page = page.click('Painting Dogs')
        assert 'Painting Cats' not in page

        assert 'Painting Dogs' in page
        assert 'Montag, 28. April 2025' in page
        assert '18:00 - 22:00' in page
        assert 'Art Gallery' in page
        assert 'Art Club' in page
