import os

from onegov.election_day.models import Subscriber
from tests.onegov.election_day.common import login
from tests.shared import Client


def test_view_email_subscription(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    # Subscribe using the form
    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = 'abcd'
    subscribe = subscribe.form.submit()
    assert "Ungültige Email-Adresse" in subscribe

    subscribe.form['email'] = 'howard@example.com'
    subscribe = subscribe.form.submit()
    assert "E-Mail-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app_zg.session().query(Subscriber).one().locale == \
        'de_CH'

    assert len(os.listdir(client.app.maildir)) == 1
    message = client.get_email(0, flush_queue=True)
    assert message['Subject'] == 'E-Mail-Benachrichtigung abonniert'
    assert message['To'] == 'howard@example.com'
    assert message['From'] == 'Kanton Govikon <mails@govikon.ch>'
    assert message['ReplyTo'] == 'Kanton Govikon <mails@govikon.ch>'
    headers = {h['Name']: h['Value'] for h in message['Headers']}
    assert '/unsubscribe-email?opaque=' in headers['List-Unsubscribe']
    assert headers['List-Unsubscribe-Post'] == 'List-Unsubscribe=One-Click'

    optout = headers['List-Unsubscribe'].strip('<>')

    html = message['HtmlBody']
    assert f'<a href="{optout}">Abmelden</a>' in html
    assert 'Die E-Mail-Benachrichtigung wurde abonniert.' in html

    # Change the language
    client.get('/locale/fr_CH').follow()
    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = 'howard@example.com'
    subscribe = subscribe.form.submit()
    assert election_day_app_zg.session().query(Subscriber).one().locale == \
        'fr_CH'
    assert len(os.listdir(client.app.maildir)) == 0

    manage = Client(election_day_app_zg)
    login(manage)
    assert 'howard@example.com' in manage.get('/manage/subscribers/email')

    # Unsubscribe using the list-unsubscribe
    Client(election_day_app_zg).post(optout)
    assert election_day_app_zg.session().query(Subscriber).count() == 0

    # Subscribe again
    client.get('/locale/de_CH').follow()
    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = 'howard@example.com'
    subscribe = subscribe.form.submit()

    assert election_day_app_zg.session().query(Subscriber).one()
    assert len(os.listdir(client.app.maildir)) == 1
    client.flush_email_queue()

    # Unsubscribe using the form
    unsubscribe = client.get('/unsubscribe-email')
    unsubscribe.form['email'] = 'abcd'
    unsubscribe = unsubscribe.form.submit()
    assert "Ungültige Email-Adresse" in unsubscribe

    unsubscribe.form['email'] = 'howard@example.com'
    unsubscribe = unsubscribe.form.submit()
    assert "E-Mail-Benachrichtigung wurde beendet." in unsubscribe
    assert len(os.listdir(client.app.maildir)) == 0


def test_view_manage_email_subscription(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = '123@example.org'
    subscribe = subscribe.form.submit()
    assert "E-Mail-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app_zg.session().query(Subscriber).one().locale == \
        'de_CH'

    subscribe = client.get('/subscribe-email')
    subscribe.form['email'] = '456@example.org'
    subscribe = subscribe.form.submit()
    assert "E-Mail-Benachrichtigung wurde abonniert" in subscribe

    login(client)
    manage = client.get('/manage/subscribers/email')
    assert '123@example.org' in manage
    assert '456@example.org' in manage

    response = client.get('/manage/subscribers/email/export')
    assert response.headers['Content-Type'] == 'text/csv; charset=UTF-8'
    assert response.headers['Content-Disposition'] == \
        'inline; filename=email-subscribers.csv'
    assert '123@example.org' in response.text
    assert '456@example.org' in response.text

    manage = client.get('/manage/subscribers/email?term=23')
    assert '123@example.org' in manage
    assert '456@example.org' not in manage

    manage.click('Löschen').click('Abbrechen')

    manage = client.get('/manage/subscribers/email?term=123')
    assert '123@example.org' in manage

    manage.click('Löschen').form.submit()

    manage = client.get('/manage/subscribers/email')
    assert '123@example.org' not in manage
    assert '456@example.org' in manage


def test_view_sms_subscription(election_day_app_zg):
    sms_path = os.path.join(
        election_day_app_zg.configuration['sms_directory'],
        election_day_app_zg.schema
    )

    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = 'abcd'
    subscribe = subscribe.form.submit()
    assert "Ungültige Telefonnummer" in subscribe

    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app_zg.session().query(Subscriber).one().locale == \
        'de_CH'
    assert len(os.listdir(sms_path)) == 1

    filename = os.listdir(sms_path)[0]
    with open(os.path.join(sms_path, filename)) as f:
        content = f.read()
        assert '+41791112233' in content
        assert 'Die SMS-Benachrichtigung wurde abonniert' in content

    client.get('/locale/fr_CH').follow()

    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert election_day_app_zg.session().query(Subscriber).one().locale == \
        'fr_CH'
    assert len(os.listdir(sms_path)) == 1

    client.get('/locale/de_CH').follow()

    login(client)
    assert '+41791112233' in client.get('/manage/subscribers/sms')
    assert 'fr_CH' in client.get('/manage/subscribers/sms')
    assert len(os.listdir(sms_path)) == 1

    unsubscribe = client.get('/unsubscribe-sms')
    unsubscribe.form['phone_number'] = 'abcd'
    unsubscribe = unsubscribe.form.submit()
    assert "Ungültige Telefonnummer" in unsubscribe

    unsubscribe.form['phone_number'] = '0791112233'
    unsubscribe = unsubscribe.form.submit()
    assert "SMS-Benachrichtigung wurde beendet." in unsubscribe
    assert len(os.listdir(sms_path)) == 1

    unsubscribe = client.get('/unsubscribe-sms')
    unsubscribe.form['phone_number'] = '0791112233'
    unsubscribe = unsubscribe.form.submit()
    assert "SMS-Benachrichtigung wurde beendet." in unsubscribe
    assert len(os.listdir(sms_path)) == 1


def test_view_manage_sms_subscription(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app_zg.session().query(Subscriber).one().locale == \
        'de_CH'

    subscribe = client.get('/subscribe-sms')
    subscribe.form['phone_number'] = '0791112244'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe

    login(client)
    manage = client.get('/manage/subscribers/sms')
    assert '+41791112233' in manage
    assert '+41791112244' in manage

    response = client.get('/manage/subscribers/sms/export')
    assert response.headers['Content-Type'] == 'text/csv; charset=UTF-8'
    assert response.headers['Content-Disposition'] == \
        'inline; filename=sms-subscribers.csv'
    assert '+41791112233' in response.text
    assert '+41791112244' in response.text

    manage = client.get('/manage/subscribers/sms?term=2233')
    assert '+41791112233' in manage
    assert '+41791112244' not in manage

    manage.click('Löschen').click('Abbrechen')

    manage = client.get('/manage/subscribers/sms?term=2233')
    assert '+41791112233' in manage

    manage.click('Löschen').form.submit()

    manage = client.get('/manage/subscribers/sms')
    assert '+41791112233' not in manage
    assert '+41791112244' in manage
