from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.tests.common import DummyRequest
from unittest.mock import Mock


def test_subscriber_collection(session):
    request = DummyRequest(locale='de_CH')

    # Add
    collection = SubscriberCollection(session)
    collection.subscribe('endpoint', request, confirm=False)
    subscriber = collection.query().one()
    assert subscriber.address == 'endpoint'
    assert subscriber.locale == 'de_CH'
    assert collection.by_id(subscriber.id) == subscriber

    # Re-add
    collection.subscribe('endpoint', request, confirm=False)
    subscriber = collection.query().one()
    assert subscriber.address == 'endpoint'
    assert subscriber.locale == 'de_CH'

    # Update locale
    collection.subscribe('endpoint', DummyRequest(locale='en'), confirm=False)
    subscriber = collection.query().one()
    assert subscriber.address == 'endpoint'
    assert subscriber.locale == 'en'

    # Add email
    email_collection = EmailSubscriberCollection(session)
    email_collection.subscribe('user@example.org', request, confirm=False)
    subscriber = email_collection.query().one()
    assert subscriber.address == 'user@example.org'
    assert subscriber.locale == 'de_CH'

    # Add SMS
    sms_collection = SmsSubscriberCollection(session)
    sms_collection.subscribe('+41791112233', request, confirm=False)
    subscriber = sms_collection.query().one()
    assert subscriber.address == '+41791112233'
    assert subscriber.locale == 'de_CH'

    # Unsubscribe
    assert collection.query().count() == 3
    email_collection.unsubscribe('+41791112233')
    email_collection.unsubscribe('endpoint')
    sms_collection.unsubscribe('user@example.org')
    sms_collection.unsubscribe('endpoint')
    assert collection.query().count() == 3

    sms_collection.unsubscribe('+41791112233')
    email_collection.unsubscribe('user@example.org')
    assert collection.query().count() == 1

    email_collection.subscribe('user@example.org', request, confirm=False)
    sms_collection.subscribe('+41791112233', request, confirm=False)
    assert collection.query().count() == 3
    collection.unsubscribe('+41791112233')
    collection.unsubscribe('user@example.org')
    collection.unsubscribe('endpoint')
    assert collection.query().count() == 0


def test_subscriber_collection_confirm_email(election_day_app, session):
    mock = Mock()
    election_day_app.send_email = mock
    request = DummyRequest(
        app=election_day_app, session=session, locale='de_CH'
    )
    collection = EmailSubscriberCollection(session)

    collection.subscribe('howard@example.org', request)
    assert mock.call_count == 1
    assert mock.call_args[1]['receivers'] == ('howard@example.org',)
    assert mock.call_args[1]['subject'] == 'E-Mail-Benachrichtigung abonniert'
    assert mock.call_args[1]['headers']['List-Unsubscribe-Post'] == (
        'List-Unsubscribe=One-Click'
    )
    assert mock.call_args[1]['headers']['List-Unsubscribe'] == (
        "<Principal/unsubscribe-email?"
        "opaque={'address': 'howard@example.org'}>"
    )

    collection.subscribe('howard@example.org', request)
    assert mock.call_count == 1

    collection.unsubscribe('howard@example.org')
    collection.subscribe('howard@example.org', request)
    assert mock.call_count == 2


def test_subscriber_collection_confirm_sms(election_day_app, session):
    mock = Mock()
    election_day_app.send_sms = mock
    request = DummyRequest(
        app=election_day_app, session=session, locale='de_CH'
    )
    collection = SmsSubscriberCollection(session)

    collection.subscribe('+41791112233', request)
    assert mock.call_count == 1
    assert mock.call_args[0][0] == '+41791112233'
    assert mock.call_args[0][1] == (
        "Die SMS-Benachrichtigung wurde abonniert. Sie erhalten in Zukunft "
        "eine SMS, sobald neue Resultate publiziert wurden."
    )

    collection.subscribe('+41791112233', request)
    assert mock.call_count == 1

    collection.unsubscribe('+41791112233')
    collection.subscribe('+41791112233', request)
    assert mock.call_count == 2


def test_subscriber_collection_pagination(session):
    request = DummyRequest(locale='de_CH')

    # Add email subscribers
    collection = EmailSubscriberCollection(session)
    for number in range(100):
        collection.subscribe(
            'user{:02}@example.org'.format(number),
            request,
            confirm=False
        )
    assert collection.query().count() == 100

    # Add SMS subscribers
    collection = SmsSubscriberCollection(session)
    for number in range(100):
        collection.subscribe(
            '+417911122{:02}'.format(number),
            request,
            confirm=False
        )
    assert collection.query().count() == 100

    assert SubscriberCollection(session).query().count() == 200

    # Test Email pagination
    assert EmailSubscriberCollection(session, page=0).batch[0].address == \
        'user00@example.org'
    assert EmailSubscriberCollection(session, page=4).batch[4].address == \
        'user44@example.org'
    assert EmailSubscriberCollection(session, page=5).batch[5].address == \
        'user55@example.org'
    assert EmailSubscriberCollection(session, page=9).batch[9].address == \
        'user99@example.org'
    assert len(EmailSubscriberCollection(session, page=10).batch) == 0

    # Test SMS pagination
    assert SmsSubscriberCollection(session, page=0).batch[0].address == \
        '+41791112200'
    assert SmsSubscriberCollection(session, page=4).batch[4].address == \
        '+41791112244'
    assert SmsSubscriberCollection(session, page=5).batch[5].address == \
        '+41791112255'
    assert SmsSubscriberCollection(session, page=9).batch[9].address == \
        '+41791112299'
    assert len(SmsSubscriberCollection(session, page=10).batch) == 0

    # Test mixed pagination
    assert SubscriberCollection(session, page=0).batch[0].address == \
        '+41791112200'
    assert SubscriberCollection(session, page=4).batch[4].address == \
        '+41791112244'
    assert SubscriberCollection(session, page=5).batch[5].address == \
        '+41791112255'
    assert SubscriberCollection(session, page=9).batch[9].address == \
        '+41791112299'
    assert SubscriberCollection(session, page=10).batch[0].address == \
        'user00@example.org'
    assert SubscriberCollection(session, page=14).batch[4].address == \
        'user44@example.org'
    assert SubscriberCollection(session, page=15).batch[5].address == \
        'user55@example.org'
    assert SubscriberCollection(session, page=19).batch[9].address == \
        'user99@example.org'
    assert len(SubscriberCollection(session, page=20).batch) == 0


def test_subscriber_collection_term(session):
    request = DummyRequest(locale='de_CH')

    # Add email subscribers
    collection = EmailSubscriberCollection(session)
    for number in range(100):
        collection.subscribe(
            'user{:02}@example.org'.format(number),
            request,
            confirm=False
        )
    assert collection.query().count() == 100

    # Add SMS subscribers
    collection = SmsSubscriberCollection(session)
    for number in range(100):
        collection.subscribe(
            '+417911122{:02}'.format(number),
            request,
            confirm=False
        )
    assert collection.query().count() == 100

    assert SubscriberCollection(session).query().count() == 200

    # Query email subscribers
    collection = SubscriberCollection(session, term='@')
    assert collection.query().count() == 100
    collection = EmailSubscriberCollection(session, term='@')
    assert collection.query().count() == 100
    collection = SmsSubscriberCollection(session, term='@')
    assert collection.query().count() == 0

    collection = SubscriberCollection(session, term='user1')
    assert collection.query().count() == 10
    collection = EmailSubscriberCollection(session, term='user1')
    assert collection.query().count() == 10
    collection = SmsSubscriberCollection(session, term='user1')
    assert collection.query().count() == 0

    collection = SubscriberCollection(session, term='user11@example.org')
    assert collection.query().one().address == 'user11@example.org'
    collection = EmailSubscriberCollection(session, term='user11@example.org')
    assert collection.query().one().address == 'user11@example.org'
    collection = SmsSubscriberCollection(session, term='user11@example.org')
    assert collection.query().first() is None

    collection = SubscriberCollection(session, term='user11')
    assert collection.query().one().address == 'user11@example.org'
    collection = EmailSubscriberCollection(session, term='user11')
    assert collection.query().one().address == 'user11@example.org'
    collection = SmsSubscriberCollection(session, term='user11')
    assert collection.query().first() is None

    # Query SMS subscribers
    collection = SubscriberCollection(session, term='+417911122')
    assert collection.query().count() == 100
    collection = EmailSubscriberCollection(session, term='+417911122')
    assert collection.query().count() == 0
    collection = SmsSubscriberCollection(session, term='+417911122')
    assert collection.query().count() == 100

    collection = SubscriberCollection(session, term='+41791112200')
    assert collection.query().one().address == '+41791112200'
    collection = EmailSubscriberCollection(session, term='+41791112200')
    assert collection.query().first() is None
    collection = SmsSubscriberCollection(session, term='+41791112200')
    assert collection.query().one().address == '+41791112200'

    collection = SubscriberCollection(session, term='2200')
    assert collection.query().one().address == '+41791112200'
    collection = EmailSubscriberCollection(session, term='2200')
    assert collection.query().first() is None
    collection = SmsSubscriberCollection(session, term='2200')
    assert collection.query().one().address == '+41791112200'

    collection = SubscriberCollection(session, term='220')
    assert collection.query().count() == 11
    collection = EmailSubscriberCollection(session, term='220')
    assert collection.query().first() is None
    collection = SmsSubscriberCollection(session, term='220')
    assert collection.query().count() == 11

    # Query mixed subscribers
    collection = SubscriberCollection(session, term='33')
    assert collection.query().count() == 2
    collection = EmailSubscriberCollection(session, term='33')
    assert collection.query().one().address == 'user33@example.org'
    collection = SmsSubscriberCollection(session, term='33')
    assert collection.query().one().address == '+41791112233'
