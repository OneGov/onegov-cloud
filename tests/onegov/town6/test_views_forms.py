import textwrap
from datetime import date

import pytest

from onegov.form import FormCollection
from onegov.ticket import Ticket
from onegov.user import UserCollection
from tests.onegov.org.common import get_mail
from tests.onegov.town6.common import step_class
import transaction
from freezegun import freeze_time

from tests.shared.utils import open_in_browser


@pytest.mark.skip('Errors in empty handler registry')
def test_form_steps(client):
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

    def register(client, data_in_email, auto_accept=False):
        nonlocal count
        count += 1
        with freeze_time('2018-01-01'):
            page = client.get('/form/meetup')
            page.form['e_mail'] = f'info{count}@example.org'
            page.form['name'] = 'Foobar'
            page = page.form.submit().follow()

            page.form['send_by_email'] = data_in_email
            page = page.form.submit().follow()
        if auto_accept:
            return page
        return client.get('/tickets/ALL/open').click("Annehmen").follow()

    client.login_editor()
    page = register(client, data_in_email=True)

    assert "bestätigen" in page
    assert "ablehnen" in page

    msg = client.app.smtp.sent[-1]
    assert "Ihre Anfrage wurde unter der folgenden Referenz registriert" in msg
    assert "Foobar" in msg

    page = page.click("Anmeldung bestätigen").follow()

    msg = client.app.smtp.sent[-1]
    assert 'Ihre Anmeldung für "Meetup" wurde bestätigt' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" in msg

    page.click("Anmeldung stornieren").follow()

    msg = client.app.smtp.sent[-1]
    assert 'Ihre Anmeldung für "Meetup" wurde storniert' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" in msg

    page = register(client, data_in_email=False)

    msg = client.app.smtp.sent[-1]
    assert "Ihre Anfrage wurde unter der folgenden Referenz registriert" in msg
    assert "Foobar" not in msg

    page.click("Anmeldung ablehnen")

    msg = client.app.smtp.sent[-1]
    assert 'Ihre Anmeldung für "Meetup" wurde abgelehnt' in msg
    assert "01.01.2018 - 31.01.2018" in msg
    assert "Foobar" not in msg

    # create one undecided submission
    open_registration = register(client, False, auto_accept=True)

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
    page = register(client, False, auto_accept=True)
    mail = get_mail(client.app.smtp.outbox, -1)
    assert '_Meetup=3A_Ihre_Anmeldung_wurde_best=C3=A4tigt?=' in mail['subject']
    assert 'Ihr Anliegen wurde abgeschlossen' in page

    # check ownership of the ticket
    client.app.session().query(Ticket).filter_by(user_id=user_id).one()

    # Reopen the last
    client.login_editor()
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
    mail = get_mail(client.app.smtp.outbox, -1)
    assert 'Message for all the attendees' in mail['html']
    assert 'Allgemeine Nachricht' in mail['subject']

    # navigate to the registration window an cancel all
    window.click('Anmeldezeitraum absagen')
    assert 'Storniert (4)' in client.get(window.request.url)
