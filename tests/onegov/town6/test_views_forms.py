import textwrap
import transaction

from datetime import date
from freezegun import freeze_time
from onegov.form import FormCollection
from onegov.ticket import Ticket
from onegov.user import UserCollection
from tests.onegov.town6.common import step_class
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
    assert broadcast.call_args[0][3] == {
        'event': 'browser-notification', 'title': 'Neues Ticket'
    }


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
