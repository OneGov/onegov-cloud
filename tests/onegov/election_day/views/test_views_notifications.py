from __future__ import annotations

import json
import os

from tests.onegov.election_day.common import create_election_compound
from tests.onegov.election_day.common import get_email_link
from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import upload_election_compound
from tests.onegov.election_day.common import upload_majorz_election
from tests.onegov.election_day.common import upload_vote
from tests.shared import Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_view_notifications_votes(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['title_de'] = "Vote"
    new.form['date'] = '2013-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    # Test retrigger messages
    assert "Benachrichtigungen auslösen" in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" in upload_vote(client, False)

    principal = election_day_app_zg.principal
    principal.webhooks = {'http://example.com/1': {}}
    election_day_app_zg.cache.set('principal', principal)

    assert "Benachrichtigungen auslösen" in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" in upload_vote(client, False)
    assert "erneut auslösen" not in client.get('/vote/vote/trigger')

    trigger = client.get('/vote/vote/trigger')
    trigger.form['notifications'] = ['webhooks']
    trigger.form.submit()

    form = client.get('/vote/vote/trigger')
    assert "erneut auslösen" in form
    assert ": webhooks (" in form

    upload_vote(client, False)
    assert "erneut auslösen" not in client.get('/vote/vote/trigger')

    # Test email and last notified
    principal = election_day_app_zg.principal
    principal.email_notification = True
    election_day_app_zg.cache.set('principal', principal)

    anom = Client(election_day_app_zg)
    anom.get('/locale/fr_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'hans@example.org'
    subscribe.form.submit()
    message = client.get_email(0, flush_queue=True)
    anom.get(get_email_link(message, 'optin'))

    anom = Client(election_day_app_zg)
    anom.get('/locale/de_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'peter@example.org'
    subscribe.form.submit()
    client.get_email(0, flush_queue=True)

    trigger = client.get('/vote/vote/trigger')
    trigger.form['notifications'] = ['email']
    trigger.form.submit()

    message = client.get_email(0, flush_queue=True)
    assert message['To'] == 'hans@example.org'
    assert message['Subject'] == 'Vote - Refusé'
    message = message['HtmlBody']
    assert "Vote - Refusé" in message


def test_view_notifications_elections(election_day_app_gr: TestApp) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = "Majorz Election"
    new.form['date'] = '2013-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    # Test retrigger messages
    assert "Benachrichtigungen auslösen" in client.get('/manage/elections')
    assert "Benachrichtigungen auszulösen" in upload_majorz_election(
        client, False
    )

    principal = election_day_app_gr.principal
    principal.webhooks = {'http://example.com/1': {}}
    election_day_app_gr.cache.set('principal', principal)

    assert "Benachrichtigungen auslösen" in client.get('/manage/elections')
    assert "Benachrichtigungen auszulösen" in upload_majorz_election(
        client, False
    )
    assert "erneut auslösen" not in client.get(
        '/election/majorz-election/trigger'
    )

    trigger = client.get('/election/majorz-election/trigger')
    trigger.form['notifications'] = ['webhooks']
    trigger.form.submit()

    form = client.get('/election/majorz-election/trigger')
    assert "erneut auslösen" in form
    assert ": webhooks (" in form

    upload_majorz_election(client, False)
    assert "erneut auslösen" not in client.get(
        '/election/majorz-election/trigger'
    )

    # Test email and last notified
    principal = election_day_app_gr.principal
    principal.email_notification = True
    election_day_app_gr.cache.set('principal', principal)

    anom = Client(election_day_app_gr)
    anom.get('/locale/fr_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'hans@example.org'
    subscribe.form.submit()

    message = client.get_email(0, flush_queue=True)
    anom.get(get_email_link(message, 'optin'))

    anom = Client(election_day_app_gr)
    anom.get('/locale/de_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'peter@example.org'
    subscribe.form.submit()
    client.get_email(0, flush_queue=True)

    trigger = client.get('/election/majorz-election/trigger')
    trigger.form['notifications'] = ['email']
    trigger.form.submit()

    message = client.get_email(0, flush_queue=True)
    assert message['To'] == 'hans@example.org'
    assert message['Subject'] == (
        'Majorz Election - Nouveaux résultats intermédiaires'
    )
    message = message['HtmlBody']
    assert "Majorz Election - Nouveaux résultats intermédiaires" in message


def test_view_notifications_election_compouds(
    election_day_app_gr: TestApp
) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    create_election_compound(client)

    # Test retrigger messages
    assert "Benachrichtigungen auslösen" in client.get(
        '/manage/election-compounds'
    )
    assert "Benachrichtigungen auszulösen" in upload_election_compound(
        client, False
    )

    principal = election_day_app_gr.principal
    principal.webhooks = {'http://example.com/1': {}}
    election_day_app_gr.cache.set('principal', principal)

    assert "Benachrichtigungen auslösen" in client.get(
        '/manage/election-compounds'
    )
    assert "Benachrichtigungen auszulösen" in upload_election_compound(
        client, False
    )
    assert "erneut auslösen" not in client.get('/elections/elections/trigger')

    trigger = client.get('/elections/elections/trigger')
    trigger.form['notifications'] = ['webhooks']
    trigger.form.submit()

    form = client.get('/elections/elections/trigger')
    assert "erneut auslösen" in form
    assert ": webhooks (" in form

    upload_election_compound(client, False)
    assert "erneut auslösen" not in client.get('/elections/elections/trigger')

    # Test email and last notified
    principal = election_day_app_gr.principal
    principal.email_notification = True
    election_day_app_gr.cache.set('principal', principal)

    anom = Client(election_day_app_gr)
    anom.get('/locale/fr_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'hans@example.org'
    subscribe.form.submit()

    message = client.get_email(0, flush_queue=True)
    anom.get(get_email_link(message, 'optin'))

    anom = Client(election_day_app_gr)
    anom.get('/locale/de_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'peter@example.org'
    subscribe.form.submit()
    client.get_email(0, flush_queue=True)

    trigger = client.get('/elections/elections/trigger')
    trigger.form['notifications'] = ['email']
    trigger.form.submit()

    message = client.get_email(0, flush_queue=True)
    assert message['To'] == 'hans@example.org'
    assert message['Subject'] == (
        'Elections - Nouveaux résultats intermédiaires'
    )
    message = message['HtmlBody']
    assert 'Elections - Nouveaux résultats intermédiaires' in message
    assert 'Winner Carol' in message
    assert 'Sieger Hans' in message


def test_view_notifications_summarized(election_day_app_zg: TestApp) -> None:
    sms_path = os.path.join(
        election_day_app_zg.sms_directory,
        election_day_app_zg.schema
    )

    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['title_de'] = "Unternehmenssteuerreformgesetz"
    new.form['date'] = '2013-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = "Regierungsratswahl"
    new.form['date'] = '2013-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'proporz'
    new.form['domain'] = 'municipality'
    new.form.submit()

    new = client.get('/manage/election-compounds/new-election-compound')
    new.form['title_de'] = "Kantonsratswahl"
    new.form['date'] = '2013-01-01'
    new.form['municipality_elections'] = ['regierungsratswahl']
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = 'municipality'
    new.form.submit()

    manage = client.get('/trigger-notifications')
    assert "Unternehmenssteuerreformgesetz" in manage
    assert "Regierungsratswahl" in manage
    assert "Kantonsratswahl" in manage
    assert "Webbhooks" not in manage
    assert "SMS" not in manage
    assert "E-Mail" not in manage

    # Add configuration
    principal = election_day_app_zg.principal
    principal.webhooks = {'http://example.com/1': {}}
    principal.email_notification = True
    principal.sms_notification = 'http://example.com'
    election_day_app_zg.cache.set('principal', principal)

    # Trigger all notification (no subscribers yet)
    manage = client.get('/trigger-notifications')
    assert "Unternehmenssteuerreformgesetz" in manage
    assert "Regierungsratswahl" in manage
    assert "Webhooks" in manage
    assert "SMS" in manage
    assert "E-Mail" in manage

    manage = client.get('/trigger-notifications')
    manage.form['notifications'] = ['webhooks', 'email', 'sms']
    manage.form['elections'] = ['regierungsratswahl']
    manage.form['election_compounds'] = ['Kantonsratswahl']
    manage.form['votes'] = ['unternehmenssteuerreformgesetz']
    manage = manage.form.submit().maybe_follow()
    assert "Benachrichtigungen ausgelöst" in manage

    assert len(os.listdir(client.app.maildir)) == 0
    assert not os.path.exists(sms_path)

    # Add subscriber (2 active, 2 inactive)
    anom = Client(election_day_app_zg)
    anom.get('/locale/fr_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'hans@example.org'
    subscribe.form.submit()
    message = client.get_email(0, flush_queue=True)
    anom.get(get_email_link(message, 'optin'))

    anom = Client(election_day_app_zg)
    anom.get('/locale/de_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'peter@example.org'
    subscribe.form.submit()
    client.get_email(0, flush_queue=True)

    subscribe = anom.get('/subscribe-sms')
    subscribe.form['phone_number'] = '+41792223344'
    subscribe.form.submit()
    assert len(os.listdir(sms_path)) == 1
    client.get('/manage/subscribers/sms').click('Deaktivieren').form.submit()

    anom.get('/locale/fr_CH').follow()
    subscribe = anom.get('/subscribe-sms')
    subscribe.form['phone_number'] = '+41792223355'
    subscribe.form.submit()
    assert len(os.listdir(sms_path)) == 2

    # Trigger all notification
    manage = client.get('/trigger-notifications')
    client.get('/manage/subscribers/email')
    manage.form['notifications'] = ['webhooks', 'email', 'sms']
    manage.form['elections'] = ['regierungsratswahl']
    manage.form['election_compounds'] = ['kantonsratswahl']
    manage.form['votes'] = ['unternehmenssteuerreformgesetz']
    manage = manage.form.submit().maybe_follow()
    assert "Benachrichtigungen ausgelöst" in manage

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0, flush_queue=True)
    assert message['To'] == 'hans@example.org'
    assert message['Subject'] == 'Les nouveaux résultats sont disponibles'

    message = message['HtmlBody']
    assert "http://localhost/unsubscribe-email" in message
    assert "<h1>Regierungsratswahl</h1>" in message
    assert "<h1>Kantonsratswahl</h1>" in message
    assert "<h1>Unternehmenssteuerreformgesetz</h1>" in message

    assert len(os.listdir(sms_path)) == 3
    contents = []
    for sms in os.listdir(sms_path):
        with open(os.path.join(sms_path, sms)) as file:
            contents.append(json.loads(file.read())['content'])

    assert (
        'Les nouveaux résultats sont disponibles sur http://example.com'
        in contents
    )

    manage = client.get('/trigger-notifications')
    assert "erneut auslösen" in manage
    assert ": E-Mail (" in manage
    assert ": SMS (" in manage
    assert ": webhooks (" in manage
