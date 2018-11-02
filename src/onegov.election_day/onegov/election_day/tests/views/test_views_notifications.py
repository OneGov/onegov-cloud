import os

from datetime import date
from onegov.election_day.tests.common import login
from onegov.election_day.tests.common import upload_majorz_election
from onegov.election_day.tests.common import upload_vote
from webtest import TestApp as Client


def test_view_notifications_votes(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Vote"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    # Test retrigger messages
    assert "Benachrichtigungen auslösen" not in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" not in upload_vote(client, False)

    principal = election_day_app.principal
    principal.webhooks = {'http://example.com/1': None}
    election_day_app.cache.set('principal', principal)

    assert "Benachrichtigungen auslösen" in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" in upload_vote(client, False)
    assert "erneut auslösen" not in client.get('/vote/vote/trigger')

    trigger = client.get('/vote/vote/trigger')
    trigger.form['notifications'] = ['webhooks']
    trigger.form.submit()

    assert "erneut auslösen" in client.get('/vote/vote/trigger')

    upload_vote(client, False)
    assert "erneut auslösen" not in client.get('/vote/vote/trigger')

    # Test email
    principal = election_day_app.principal
    principal.email_notification = True
    election_day_app.cache.set('principal', principal)

    anom = Client(election_day_app)
    anom.get('/locale/fr_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'hans@example.org'
    subscribe.form.submit()

    trigger = client.get('/vote/vote/trigger')
    trigger.form['notifications'] = ['email']
    trigger.form.submit()

    message = election_day_app.smtp.outbox.pop()
    assert message['To'] == 'hans@example.org'
    assert message['Subject'] == '=?utf-8?q?Vote_-_Refus=C3=A9?='
    unsubscribe = message['List-Unsubscribe'].strip('<>')

    message = message.get_payload(1).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "http://localhost/unsubscribe-email" in message
    assert "Vote - Refusé" in message

    assert 'hans@example.org' in client.get('/manage/subscribers/email')
    anom.post(unsubscribe)
    assert 'hans@example.org' not in client.get('/manage/subscribers/email')


def test_view_notifications_elections(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Majorz Election"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    # Test retrigger messages
    assert "Benachrichtigungen auslösen" not in client.get('/manage/elections')
    assert "Benachrichtigungen auszulösen" not in upload_majorz_election(
        client, False
    )

    principal = election_day_app_gr.principal
    principal.webhooks = {'http://example.com/1': None}
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

    assert "erneut auslösen" in client.get('/election/majorz-election/trigger')

    upload_majorz_election(client, False)
    assert "erneut auslösen" not in client.get(
        '/election/majorz-election/trigger'
    )

    # Test email
    principal = election_day_app_gr.principal
    principal.email_notification = True
    election_day_app_gr.cache.set('principal', principal)

    anom = Client(election_day_app_gr)
    anom.get('/locale/fr_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'hans@example.org'
    subscribe.form.submit()

    trigger = client.get('/election/majorz-election/trigger')
    trigger.form['notifications'] = ['email']
    trigger.form.submit()

    message = election_day_app_gr.smtp.outbox.pop()
    assert message['To'] == 'hans@example.org'
    assert message['Subject'] == (
        '=?utf-8?q?Majorz_Election_-_'
        'Nouveaux_r=C3=A9sultats_interm=C3=A9diaires?='
    )
    unsubscribe = message['List-Unsubscribe'].strip('<>')

    message = message.get_payload(1).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "http://localhost/unsubscribe-email" in message
    assert "Majorz Election - Nouveaux résultats intermédiaires" in message
    assert unsubscribe in message

    assert 'hans@example.org' in client.get('/manage/subscribers/email')
    assert 'hans@example.org' in anom.get(unsubscribe)
    anom.post(unsubscribe)
    assert 'hans@example.org' not in client.get('/manage/subscribers/email')


def test_view_notifications_summarized(election_day_app):
    sms_path = os.path.join(
        election_day_app.configuration['sms_directory'],
        election_day_app.schema
    )

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Unternehmenssteuerreformgesetz"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Regierungsratswahl"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    manage = client.get('/trigger-notifications')
    assert "Unternehmenssteuerreformgesetz" in manage
    assert "Regierungsratswahl" in manage
    assert "Webbhooks" not in manage
    assert "SMS" not in manage
    assert "E-Mail" not in manage

    # Add configuration
    principal = election_day_app.principal
    principal.webhooks = {'http://example.com/1': None}
    principal.email_notification = True
    principal.sms_notification = 'http://example.com'
    election_day_app.cache.set('principal', principal)

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
    manage.form['votes'] = ['unternehmenssteuerreformgesetz']
    manage = manage.form.submit().maybe_follow()
    assert "Benachrichtigungen ausgelöst" in manage

    assert len(election_day_app.smtp.outbox) == 0
    assert not os.path.exists(sms_path)

    # Add subscriber
    anom = Client(election_day_app)
    anom.get('/locale/fr_CH').follow()
    subscribe = anom.get('/subscribe-email')
    subscribe.form['email'] = 'hans@example.org'
    subscribe.form.submit()
    assert len(election_day_app.smtp.outbox) == 1
    election_day_app.smtp.outbox.pop()

    subscribe = anom.get('/subscribe-sms')
    subscribe.form['phone_number'] = '+41792223344'
    subscribe.form.submit()
    assert len(os.listdir(sms_path)) == 1

    # Trigger all notification
    manage = client.get('/trigger-notifications')
    client.get('/manage/subscribers/email')
    manage.form['notifications'] = ['webhooks', 'email', 'sms']
    manage.form['elections'] = ['regierungsratswahl']
    manage.form['votes'] = ['unternehmenssteuerreformgesetz']
    manage = manage.form.submit().maybe_follow()
    assert "Benachrichtigungen ausgelöst" in manage

    assert len(election_day_app.smtp.outbox) == 1
    message = election_day_app.smtp.outbox.pop()
    assert message['To'] == 'hans@example.org'
    assert message['Subject'] == (
        '=?utf-8?q?Les_nouveaux_r=C3=A9sultats_sont_disponibles?='
    )
    unsubscribe = message['List-Unsubscribe'].strip('<>')

    message = message.get_payload(1).get_payload(decode=True)
    message = message.decode('utf-8')
    assert "http://localhost/unsubscribe-email" in message
    assert "<h1>Regierungsratswahl</h1>" in message
    assert "<h1>Unternehmenssteuerreformgesetz</h1>" in message

    assert 'hans@example.org' in client.get('/manage/subscribers/email')
    anom.post(unsubscribe)
    assert 'hans@example.org' not in client.get('/manage/subscribers/email')

    assert len(os.listdir(sms_path)) == 2
    contents = []
    for sms in os.listdir(sms_path):
        with open(os.path.join(sms_path, sms)) as file:
            contents.append(file.read())

    assert (
        'Les nouveaux résultats sont disponibles sur http://example.com'
        in contents
    )
