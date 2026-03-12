from __future__ import annotations

import os

from onegov.election_day.models import Subscriber
from tests.onegov.election_day.common import get_email_link
from tests.onegov.election_day.common import login
from tests.shared import Client
from webtest.forms import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_view_email_subscription(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    # Subscribe with invalid email
    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = 'abcd'
    subscribe = subscribe.form.submit()
    assert "Ungültige Email-Adresse" in subscribe

    # Subscribe
    subscribe.form['email'] = 'howard@example.com'
    subscribe = subscribe.form.submit()
    assert "Sie erhalten in Kürze eine E-Mail" in subscribe

    message = client.get_email(0, flush_queue=True)
    assert message['Subject'] == 'Bitte bestätigen Sie Ihre E-Mail-Adresse'
    assert message['To'] == 'howard@example.com'
    assert message['From'] == 'Kanton Govikon <mails@govikon.ch>'
    assert message['ReplyTo'] == 'Kanton Govikon <mails@govikon.ch>'
    headers = {h['Name']: h['Value'] for h in message['Headers']}
    assert '/optout-email?opaque=' in headers['List-Unsubscribe']
    assert headers['List-Unsubscribe-Post'] == 'List-Unsubscribe=One-Click'
    optout = headers['List-Unsubscribe'].strip('<>')
    html = message['HtmlBody']
    assert f'<a href="{optout}">Abmelden</a>' in html
    assert 'Bitte bestätigen Sie Ihre E-Mail-Adresse' in html

    # Opt-in
    optin = get_email_link(message, 'optin')
    subscribe = client.get(optin)
    assert "E-Mail-Benachrichtigung wurde abonniert" in subscribe

    # Opt-in again
    subscribe = client.get(optin)
    assert "E-Mail-Benachrichtigung wurde abonniert" in subscribe

    # Subscribe and opt-in again with different locale
    client.get('/locale/fr_CH').follow()
    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = 'howard@example.com'
    subscribe = subscribe.form.submit()

    message = client.get_email(0, flush_queue=True)
    assert message['Subject'] == 'Veuillez confirmer votre e-mail'

    subscribe = client.get(get_email_link(message, 'optin'))
    assert "Vous avez souscrit avec succès" in subscribe

    # Check in backend
    manage = Client(election_day_app_zg)
    login(manage)
    subscribers = manage.get('/manage/subscribers/email')
    assert 'howard@example.com' in subscribers
    assert 'fr_CH' in subscribers
    assert '✔︎' in subscribers

    # Unsubscribe using the list-unsubscribe
    Client(election_day_app_zg).post(optout)
    assert election_day_app_zg.session().query(
        Subscriber).one().active is False

    # Opt-in again
    client.get('/locale/de_CH').follow()
    subscribe = client.get(optin)
    assert "E-Mail-Benachrichtigung wurde abonniert" in subscribe

    # Unsubscribe with invalid email
    unsubscribe = client.get('/unsubscribe-email')
    unsubscribe.form['email'] = 'abcd'
    unsubscribe = unsubscribe.form.submit()
    assert "Ungültige Email-Adresse" in unsubscribe

    # Unsubscribe
    unsubscribe = client.get('/unsubscribe-email')
    unsubscribe.form['email'] = 'howard@example.com'
    unsubscribe = unsubscribe.form.submit()
    assert "Sie erhalten in Kürze eine E-Mail" in unsubscribe

    message = client.get_email(0, flush_queue=True)
    assert message['Subject'] == 'Bitte bestätigen Sie Ihre Abmeldung'
    assert message['To'] == 'howard@example.com'
    assert message['From'] == 'Kanton Govikon <mails@govikon.ch>'
    assert message['ReplyTo'] == 'Kanton Govikon <mails@govikon.ch>'
    headers = {h['Name']: h['Value'] for h in message['Headers']}
    assert '/optout-email?opaque=' in headers['List-Unsubscribe']
    assert headers['List-Unsubscribe-Post'] == 'List-Unsubscribe=One-Click'
    optout = headers['List-Unsubscribe'].strip('<>')
    html = message['HtmlBody']
    assert f'<a href="{optout}">Abmelden</a>' in html
    assert 'Bitte bestätigen Sie Ihre Abmeldung' in html

    # Opt-out
    unsubscribe = client.get(optout)
    assert "Die E-Mail-Benachrichtigung wurde beendet." in unsubscribe

    # Opt-out again
    unsubscribe = client.get(optout)
    assert "Die E-Mail-Benachrichtigung wurde beendet." in unsubscribe

    # Subscribe and un-subscribe with specific domain
    principal = election_day_app_zg.principal
    principal.segmented_notifications = True
    election_day_app_zg.cache.set('principal', principal)

    # NOTE: this section may depend on static data for principle.entities.
    # See src/onegov/election_day/static/municipalities/<year>/*.json
    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = 'howard@example.com'
    subscribe.form['domain'].select('municipality')
    subscribe.form['domain_segment'].select('Zug')
    subscribe = subscribe.form.submit()
    assert "Sie erhalten in Kürze eine E-Mail" in subscribe

    message = client.get_email(0, flush_queue=True)
    optin = get_email_link(message, 'optin')
    subscribe = client.get(optin)
    assert "E-Mail-Benachrichtigung wurde abonniert" in subscribe

    unsubscribe = client.get('/unsubscribe-email')
    unsubscribe.form['email'] = 'howard@example.com'
    unsubscribe.form['domain'].select('municipality')
    unsubscribe.form['domain_segment'].select('Zug')
    unsubscribe = unsubscribe.form.submit()
    assert "Sie erhalten in Kürze eine E-Mail" in unsubscribe

    message = client.get_email(0, flush_queue=True)
    optout = get_email_link(message, 'optout')
    unsubscribe = client.get(optout)
    assert "Die E-Mail-Benachrichtigung wurde beendet." in unsubscribe


def test_view_manage_email_subscription(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    # Add two subscriptions
    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = '123@example.org'
    subscribe = subscribe.form.submit()
    message = client.get_email(0, flush_queue=True)
    subscribe = client.get(get_email_link(message, 'optin'))
    assert "E-Mail-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app_zg.session().query(
        Subscriber).one().locale == 'de_CH'

    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = '456@example.org'
    subscribe = subscribe.form.submit()
    message = client.get_email(0, flush_queue=True)
    subscribe = client.get(get_email_link(message, 'optin'))
    assert "E-Mail-Benachrichtigung wurde abonniert" in subscribe

    # View
    login(client)
    manage = client.get('/manage/subscribers/email')
    assert '123@example.org' in manage
    assert '456@example.org' in manage

    # Deactivate
    manage.click('Deaktivieren', index=1).form.submit().follow()
    manage = client.get('/manage/subscribers/email')
    assert '✘︎' in manage

    # Activate
    manage.click('Aktivieren').form.submit().follow()
    manage = client.get('/manage/subscribers/email')
    assert '✘︎' not in manage

    # Export
    response = client.get('/manage/subscribers/email/export')
    assert response.headers['Content-Type'] == 'text/csv; charset=UTF-8'
    assert response.headers['Content-Disposition'] == (
        'inline; filename=email-subscribers.csv')
    export = response.text
    assert '123@example.org' in export
    assert '456@example.org' in export

    # Search
    manage = client.get('/manage/subscribers/email?term=23')
    assert '123@example.org' in manage
    assert '456@example.org' not in manage

    # Delete
    manage.click('Löschen').click('Abbrechen')

    manage = client.get('/manage/subscribers/email?term=123')
    assert '123@example.org' in manage

    manage.click('Löschen').form.submit()

    manage = client.get('/manage/subscribers/email')
    assert '123@example.org' not in manage
    assert '456@example.org' in manage

    # Cleanup
    manage = manage.click('Bereinigen')
    manage.form['type'] = 'deactivate'
    manage.form['file'] = Upload(
        'data.csv', export.encode('utf-8'), 'text/plain'
    )
    manage = manage.form.submit().follow()
    assert '1 Abonnenten bereinigt.' in manage

    manage = manage.click('Bereinigen')
    manage.form['type'] = 'delete'
    manage.form['file'] = Upload(
        'data.csv', export.encode('utf-8'), 'text/plain'
    )
    manage = manage.form.submit().follow()
    assert '1 Abonnenten bereinigt.' in manage

    manage = client.get('/manage/subscribers/email')
    assert '123@example.org' not in manage
    assert '456@example.org' not in manage


def test_view_sms_subscription(election_day_app_zg: TestApp) -> None:
    sms_path = os.path.join(
        election_day_app_zg.sms_directory,
        election_day_app_zg.schema
    )

    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    # Subscribe with invalid phone number
    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = 'abcd'
    subscribe = subscribe.form.submit()
    assert "Ungültige Telefonnummer" in subscribe

    # Subscribe
    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert len(os.listdir(sms_path)) == 1

    filename = os.listdir(sms_path)[0]
    with open(os.path.join(sms_path, filename)) as f:
        content = f.read()
        assert '+41791112233' in content
        assert 'Die SMS-Benachrichtigung wurde abonniert' in content

    # Subscribe again
    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert len(os.listdir(sms_path)) == 1

    # Subscribe with different locale
    client.get('/locale/fr_CH').follow()

    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert election_day_app_zg.session().query(
        Subscriber).one().locale == 'fr_CH'
    assert len(os.listdir(sms_path)) == 2

    client.get('/locale/de_CH').follow()

    # Check if created
    login(client)
    manage = client.get('/manage/subscribers/sms')
    assert '+41791112233' in manage
    assert 'fr_CH' in manage
    assert '✔︎' in manage

    # Unusubscribe with invalid phone number
    unsubscribe = client.get('/unsubscribe-sms')
    unsubscribe.form['phone_number'] = 'abcd'
    unsubscribe = unsubscribe.form.submit()
    assert "Ungültige Telefonnummer" in unsubscribe

    # Unusubscribe
    unsubscribe.form['phone_number'] = '0791112233'
    unsubscribe = unsubscribe.form.submit()
    assert "SMS-Benachrichtigung wurde beendet." in unsubscribe
    assert len(os.listdir(sms_path)) == 2

    # Unsubscribe again
    unsubscribe = client.get('/unsubscribe-sms')
    unsubscribe.form['phone_number'] = '0791112233'
    unsubscribe = unsubscribe.form.submit()
    assert "SMS-Benachrichtigung wurde beendet." in unsubscribe
    assert len(os.listdir(sms_path)) == 2

    # Subscribe and un-subscribe with specific domain
    principal = election_day_app_zg.principal
    principal.segmented_notifications = True
    election_day_app_zg.cache.set('principal', principal)

    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = '0791112233'
    subscribe.form['domain'].select('municipality')
    subscribe.form['domain_segment'].select('Zug')
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert len(os.listdir(sms_path)) == 3

    unsubscribe = client.get('/unsubscribe-sms')
    unsubscribe.form['phone_number'] = '0791112233'
    unsubscribe.form['domain'].select('municipality')
    unsubscribe.form['domain_segment'].select('Zug')
    unsubscribe = unsubscribe.form.submit()
    assert "SMS-Benachrichtigung wurde beendet" in unsubscribe
    assert len(os.listdir(sms_path)) == 3


def test_view_manage_sms_subscription(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    # Add two subscriptions
    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app_zg.session().query(
        Subscriber).one().locale == 'de_CH'

    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = '0791112244'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe

    # View
    login(client)
    manage = client.get('/manage/subscribers/sms')
    assert '+41791112233' in manage
    assert '+41791112244' in manage

    # Deactivate
    manage.click('Deaktivieren', index=1).form.submit().follow()
    manage = client.get('/manage/subscribers/sms')
    assert '✘︎' in manage

    # Activate
    manage.click('Aktivieren').form.submit().follow()
    manage = client.get('/manage/subscribers/sms')
    assert '✘︎' not in manage

    # Export
    response = client.get('/manage/subscribers/sms/export')
    assert response.headers['Content-Type'] == 'text/csv; charset=UTF-8'
    assert response.headers['Content-Disposition'] == (
        'inline; filename=sms-subscribers.csv')
    export = response.text
    assert '+41791112233' in export
    assert '+41791112244' in export

    # Search
    manage = client.get('/manage/subscribers/sms?term=2233')
    assert '+41791112233' in manage
    assert '+41791112244' not in manage

    # Delete
    manage.click('Löschen').click('Abbrechen')

    manage = client.get('/manage/subscribers/sms?term=2233')
    assert '+41791112233' in manage

    manage.click('Löschen').form.submit()

    manage = client.get('/manage/subscribers/sms')
    assert '+41791112233' not in manage
    assert '+41791112244' in manage

    # Cleanup
    manage = manage.click('Bereinigen')
    manage.form['type'] = 'deactivate'
    manage.form['file'] = Upload(
        'data.csv', export.encode('utf-8'), 'text/plain'
    )
    manage = manage.form.submit().follow()
    assert '1 Abonnenten bereinigt.' in manage

    manage = manage.click('Bereinigen')
    manage.form['type'] = 'delete'
    manage.form['file'] = Upload(
        'data.csv', export.encode('utf-8'), 'text/plain'
    )
    manage = manage.form.submit().follow()
    assert '1 Abonnenten bereinigt.' in manage

    manage = client.get('/manage/subscribers/sms')
    assert '+41791112233' not in manage
    assert '+41791112244' not in manage
