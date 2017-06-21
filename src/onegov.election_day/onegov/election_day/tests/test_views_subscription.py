import os

from onegov.election_day.models import Subscriber
from onegov.election_day.tests import login
from webtest import TestApp as Client


def test_view_subscription(election_day_app):
    sms_path = os.path.join(
        election_day_app.configuration['sms_directory'],
        election_day_app.schema
    )

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    subscribe = client.get('/subscribe')
    subscribe.form['phone_number'] = 'abcd'
    subscribe = subscribe.form.submit()
    assert "Ungültige Telefonnummer" in subscribe

    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app.session().query(Subscriber).one().locale == 'de_CH'
    assert len(os.listdir(sms_path)) == 1

    filename = os.listdir(sms_path)[0]
    assert '+41791112233' in filename
    with open(os.path.join(sms_path, filename)) as f:
        assert 'Die SMS-Benachrichtigung wurde abonniert' in f.read()

    client.get('/locale/fr_CH').follow()

    subscribe = client.get('/subscribe')
    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert election_day_app.session().query(Subscriber).one().locale == 'fr_CH'
    assert len(os.listdir(sms_path)) == 1

    client.get('/locale/de_CH').follow()

    login(client)
    assert '+41791112233' in client.get('/manage/subscribers')
    assert 'fr_CH' in client.get('/manage/subscribers')
    assert len(os.listdir(sms_path)) == 1

    unsubscribe = client.get('/unsubscribe')
    unsubscribe.form['phone_number'] = 'abcd'
    unsubscribe = unsubscribe.form.submit()
    assert "Ungültige Telefonnummer" in unsubscribe

    unsubscribe.form['phone_number'] = '0791112233'
    unsubscribe = unsubscribe.form.submit()
    assert "SMS-Benachrichtigung wurde beendet." in unsubscribe
    assert len(os.listdir(sms_path)) == 1

    unsubscribe = client.get('/unsubscribe')
    unsubscribe.form['phone_number'] = '0791112233'
    unsubscribe = unsubscribe.form.submit()
    assert "SMS-Benachrichtigung wurde beendet." in unsubscribe
    assert len(os.listdir(sms_path)) == 1


def test_view_manage_subscription(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    subscribe = client.get('/subscribe')
    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app.session().query(Subscriber).one().locale == 'de_CH'

    subscribe = client.get('/subscribe')
    subscribe.form['phone_number'] = '0791112244'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe

    login(client)
    manage = client.get('/manage/subscribers')
    assert '+41791112233' in manage
    assert '+41791112244' in manage

    manage = client.get('/manage/subscribers?term=2233')
    assert '+41791112233' in manage
    assert '+41791112244' not in manage

    manage.click('Löschen').click('Abbrechen')

    manage = client.get('/manage/subscribers?term=2233')
    assert '+41791112233' in manage

    manage.click('Löschen').form.submit()

    manage = client.get('/manage/subscribers')
    assert '+41791112233' not in manage
    assert '+41791112244' in manage
