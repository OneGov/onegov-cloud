from __future__ import annotations

import pytest

from io import BytesIO
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import SubscriberCollection
from tests.onegov.election_day.common import DummyRequest
from unittest.mock import Mock


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


def test_subscriber_collection(session: Session) -> None:
    # add generic
    collection: SubscriberCollection[Any]
    collection = SubscriberCollection(session)
    collection.add('endpoint', 'municipality', 'Govikon', 'de_CH', True)
    subscriber = collection.query().one()
    assert subscriber.address == 'endpoint'
    assert subscriber.domain == 'municipality'
    assert subscriber.domain_segment == 'Govikon'
    assert subscriber.locale == 'de_CH'
    assert collection.by_id(subscriber.id) == subscriber
    assert collection.by_address(
        'endpoint', 'municipality', 'Govikon') == subscriber

    # add email
    collection = EmailSubscriberCollection(session)
    collection.add('a@example.org', 'municipality', 'Govikon', 'fr_CH', True)
    subscriber = collection.query().one()
    assert subscriber.address == 'a@example.org'
    assert subscriber.domain == 'municipality'
    assert subscriber.domain_segment == 'Govikon'
    assert subscriber.locale == 'fr_CH'
    assert collection.by_id(subscriber.id) == subscriber
    assert collection.by_address(
        'a@example.org', 'municipality', 'Govikon') == subscriber

    # add sms
    collection = SmsSubscriberCollection(session)
    collection.add('+41791112233', 'municipality', 'Govikon', 'it_CH', True)
    subscriber = collection.query().one()
    assert subscriber.address == '+41791112233'
    assert subscriber.domain == 'municipality'
    assert subscriber.domain_segment == 'Govikon'
    assert subscriber.locale == 'it_CH'
    assert collection.by_id(subscriber.id) == subscriber
    assert collection.by_address(
        '+41791112233', 'municipality', 'Govikon') == subscriber

    # active_only
    subscriber.active = False
    collection = SubscriberCollection(session)
    assert collection.query().count() == 2
    assert collection.query(active_only=False).count() == 3
    collection = collection.for_active_only(False)
    assert collection.query().count() == 3
    assert collection.query(active_only=False).count() == 3


def test_subscriber_collection_subscribe_email(
    election_day_app_zg: TestApp
) -> None:

    mock = Mock()
    election_day_app_zg.send_marketing_email = mock  # type: ignore[method-assign]
    session = election_day_app_zg.session()
    request: Any = DummyRequest(
        app=election_day_app_zg, session=session, locale='de_CH'
    )
    collection = EmailSubscriberCollection(session, active_only=False)

    # Unsubscribe but not yet subscribed
    collection.initiate_unsubscription('hue@the.org', None, None, request)
    assert mock.call_count == 0
    assert collection.query().count() == 0

    # Initiate
    collection.initiate_subscription('hue@the.org', None, None, request)
    assert mock.call_count == 1
    assert mock.call_args[-1]['receivers'] == ('hue@the.org',)
    assert mock.call_args[-1]['subject'] == (
        'Bitte bestätigen Sie Ihre E-Mail-Adresse'
    )
    assert mock.call_args[-1]['headers']['List-Unsubscribe-Post'] == (
        'List-Unsubscribe=One-Click'
    )
    assert mock.call_args[-1]['headers']['List-Unsubscribe'] == (
        "<Principal/optout-email?"
        "opaque={'address': 'hue@the.org', 'domain': None, "
        "'domain_segment': None, 'locale': 'de_CH'}>"
    )
    assert (
        "Principal/optout-email?"
        "opaque={'address': 'hue@the.org', 'domain': None, "
        "'domain_segment': None, 'locale': 'de_CH'}"
    ) in mock.call_args[-1]['content']
    assert (
        "Principal/optin-email?"
        "opaque={'address': 'hue@the.org', 'domain': None, "
        "'domain_segment': None, 'locale': 'de_CH'}"
    ) in mock.call_args[-1]['content']
    subscriber = collection.query().one()
    assert subscriber.active is False
    assert subscriber.locale == 'de_CH'
    assert subscriber.address == 'hue@the.org'
    assert subscriber.active_since is None
    assert subscriber.inactive_since is None

    # Initiate again to send the email again
    collection.initiate_subscription('hue@the.org', None, None, request)
    assert mock.call_count == 2
    assert collection.query().one().active is False

    # Unsubscribe, but not yet confirmed
    collection.initiate_unsubscription('hue@the.org', None, None, request)
    assert mock.call_count == 3
    assert mock.call_args[-1]['receivers'] == ('hue@the.org',)
    assert mock.call_args[-1]['subject'] == (
        'Bitte bestätigen Sie Ihre Abmeldung'
    )
    assert mock.call_args[-1]['headers']['List-Unsubscribe-Post'] == (
        'List-Unsubscribe=One-Click'
    )
    assert mock.call_args[-1]['headers']['List-Unsubscribe'] == (
        "<Principal/optout-email?"
        "opaque={'address': 'hue@the.org', 'domain': None, "
        "'domain_segment': None}>"
    )
    assert (
        "Principal/optout-email?"
        "opaque={'address': 'hue@the.org', 'domain': None, "
        "'domain_segment': None}"
    ) in mock.call_args[-1]['content']
    assert collection.query().one().active is False

    # Confirm
    assert collection.confirm_subscription('hue@the.org', None, None, 'de_CH')
    subscriber = collection.query().one()
    assert subscriber.active is True
    assert subscriber.locale == 'de_CH'
    assert subscriber.address == 'hue@the.org'
    assert subscriber.active_since is not None
    assert subscriber.inactive_since is None
    activated = subscriber.active_since

    # Confirm again
    assert collection.confirm_subscription('hue@the.org', None, None, 'de_CH')
    subscriber = collection.query().one()
    assert subscriber.active is True
    assert subscriber.locale == 'de_CH'
    assert subscriber.address == 'hue@the.org'
    # should still be the same
    assert subscriber.active_since == activated
    assert subscriber.inactive_since is None

    # Confirm with wrong email
    assert not collection.confirm_subscription('h1e@z.g', None, None, 'de_CH')

    # Initiate again with different locale, but already confirmed
    request.locale = 'fr_CH'
    collection.initiate_subscription('hue@the.org', None, None, request)
    assert mock.call_count == 4
    subscriber = collection.query().one()
    assert subscriber.active is True
    assert subscriber.locale == 'de_CH'
    assert subscriber.address == 'hue@the.org'

    # Confirm to change locale
    assert collection.confirm_subscription('hue@the.org', None, None, 'fr_CH')
    subscriber = collection.query().one()
    assert subscriber.active is True
    assert subscriber.locale == 'fr_CH'
    assert subscriber.address == 'hue@the.org'
    # should still be the same
    assert subscriber.active_since == activated
    assert subscriber.inactive_since is None

    # Unsubscribe
    collection.initiate_unsubscription('hue@the.org', None, None, request)
    assert mock.call_count == 5
    subscriber = collection.query().one()
    assert subscriber.active is True
    assert subscriber.active_since == activated
    assert subscriber.inactive_since is None

    # Unusbscribe again
    collection.initiate_unsubscription('hue@the.org', None, None, request)
    assert mock.call_count == 6
    subscriber = collection.query().one()
    assert subscriber.active is True
    assert subscriber.active_since == activated
    assert subscriber.inactive_since is None

    # Cofirm unsubscription
    assert collection.confirm_unsubscription('hue@the.org', None, None)
    subscriber = collection.query().one()
    assert subscriber.active is False
    assert subscriber.active_since == activated
    assert subscriber.inactive_since is not None
    deactivated = subscriber.inactive_since

    # Cofirm unsubscription again
    assert collection.confirm_unsubscription('hue@the.org', None, None)
    subscriber = collection.query().one()
    assert subscriber.active is False
    assert subscriber.active_since == activated
    assert subscriber.inactive_since == deactivated

    # Cofirm unsubscription with wrong email
    assert not collection.confirm_unsubscription('g1@1.org', None, None)
    assert collection.query().one().active is False

    # Confirm email again to reactivate
    assert collection.confirm_subscription('hue@the.org', None, None, 'de_CH')
    subscriber = collection.query().one()
    assert subscriber.active is True
    assert subscriber.active_since is not None
    assert subscriber.active_since > activated
    assert subscriber.inactive_since is None

    # Additionally subscribe only for a segment
    collection.initiate_subscription('hue@the.org', 'a', 'b', request)
    assert mock.call_count == 7
    assert mock.call_args[-1]['headers']['List-Unsubscribe'] == (
        "<Principal/optout-email?"
        "opaque={'address': 'hue@the.org', 'domain': 'a', "
        "'domain_segment': 'b', 'locale': 'fr_CH'}>"
    )
    assert (
        "Principal/optout-email?"
        "opaque={'address': 'hue@the.org', 'domain': 'a', "
        "'domain_segment': 'b', 'locale': 'fr_CH'}"
    ) in mock.call_args[-1]['content']
    assert collection.confirm_subscription('hue@the.org', 'a', 'b', 'fr_CH')
    assert {(s.domain, s.domain_segment) for s in collection.query()} == {
        (None, None), ('a', 'b')
    }


def test_subscriber_collection_subscribe_sms(
    election_day_app_zg: TestApp
) -> None:

    mock = Mock()
    election_day_app_zg.send_sms = mock  # type: ignore[method-assign]
    session = election_day_app_zg.session()
    request: Any = DummyRequest(
        app=election_day_app_zg, session=session, locale='de_CH'
    )
    collection = SmsSubscriberCollection(session, active_only=False)

    # Unsubscribe but not existing
    collection.initiate_unsubscription('+41791112233', None, None, request)
    assert collection.query().count() == 0

    # Subscribe
    collection.initiate_subscription('+41791112233', None, None, request)
    assert mock.call_count == 1
    assert mock.call_args[0][0] == '+41791112233'
    assert mock.call_args[0][1] == (
        "Die SMS-Benachrichtigung wurde abonniert. Sie erhalten in Zukunft "
        "eine SMS, sobald neue Resultate publiziert wurden."
    )
    subscriber = collection.query().one()
    assert subscriber.address == '+41791112233'
    assert subscriber.domain is None
    assert subscriber.domain_segment is None
    assert subscriber.locale == 'de_CH'
    assert subscriber.active is True
    assert subscriber.active_since is not None
    assert subscriber.inactive_since is None
    activated = subscriber.active_since

    # Subscribe again with different locale
    request.locale = 'fr_CH'
    collection.initiate_subscription('+41791112233', None, None, request)
    assert mock.call_count == 2
    subscriber = collection.query().one()
    assert subscriber.address == '+41791112233'
    assert subscriber.domain is None
    assert subscriber.domain_segment is None
    assert subscriber.locale == 'fr_CH'
    assert subscriber.active is True
    assert subscriber.active_since == activated
    assert subscriber.inactive_since is None

    # Unsubscribe
    collection.initiate_unsubscription('+41791112233', None, None, request)
    subscriber = collection.query().one()
    assert subscriber.active is False
    assert subscriber.active_since == activated
    assert subscriber.inactive_since is not None
    deactivated = subscriber.inactive_since

    # Unsubscribe again
    collection.initiate_unsubscription('+41791112233', None, None, request)
    subscriber = collection.query().one()
    assert subscriber.active is False
    assert subscriber.active_since == activated
    assert subscriber.inactive_since == deactivated

    # Subscribe again
    collection.initiate_subscription('+41791112233', None, None, request)
    assert mock.call_count == 3
    subscriber = collection.query().one()
    assert subscriber.active is True
    assert subscriber.active_since is not None
    assert subscriber.active_since > activated
    assert subscriber.inactive_since is None

    # Additionally subscribe only for a segment
    collection.initiate_subscription('+41791112233', 'a', 'b', request)
    assert mock.call_count == 4
    assert {(s.domain, s.domain_segment) for s in collection.query()} == {
        (None, None), ('a', 'b')
    }


def test_subscriber_collection_pagination(session: Session) -> None:
    collection: SubscriberCollection[Any]
    # Add email subscribers
    collection = EmailSubscriberCollection(session)
    for number in range(100):
        collection.add(
            'user{:02}@example.org'.format(number),
            None,
            None,
            'de_CH',
            True
        )
    assert collection.query().count() == 100

    # Add SMS subscribers
    collection = SmsSubscriberCollection(session)
    for number in range(100):
        collection.add(
            '+417911122{:02}'.format(number),
            None,
            None,
            'de_CH',
            True
        )
    assert collection.query().count() == 100

    assert SubscriberCollection(session).query().count() == 200

    # Test Email pagination
    assert EmailSubscriberCollection(
        session, page=0).batch[0].address == 'user00@example.org'
    assert EmailSubscriberCollection(
        session, page=4).batch[4].address == 'user44@example.org'
    assert EmailSubscriberCollection(
        session, page=5).batch[5].address == 'user55@example.org'
    assert EmailSubscriberCollection(
        session, page=9).batch[9].address == 'user99@example.org'
    assert len(EmailSubscriberCollection(session, page=10).batch) == 0

    # Test SMS pagination
    assert SmsSubscriberCollection(
        session, page=0).batch[0].address == '+41791112200'
    assert SmsSubscriberCollection(
        session, page=4).batch[4].address == '+41791112244'
    assert SmsSubscriberCollection(
        session, page=5).batch[5].address == '+41791112255'
    assert SmsSubscriberCollection(
        session, page=9).batch[9].address == '+41791112299'
    assert len(SmsSubscriberCollection(session, page=10).batch) == 0

    # Test mixed pagination
    assert SubscriberCollection(
        session, page=0).batch[0].address == '+41791112200'
    assert SubscriberCollection(
        session, page=4).batch[4].address == '+41791112244'
    assert SubscriberCollection(
        session, page=5).batch[5].address == '+41791112255'
    assert SubscriberCollection(
        session, page=9).batch[9].address == '+41791112299'
    assert SubscriberCollection(
        session, page=10).batch[0].address == 'user00@example.org'
    assert SubscriberCollection(
        session, page=14).batch[4].address == 'user44@example.org'
    assert SubscriberCollection(
        session, page=15).batch[5].address == 'user55@example.org'
    assert SubscriberCollection(
        session, page=19).batch[9].address == 'user99@example.org'
    assert len(SubscriberCollection(session, page=20).batch) == 0


def test_subscriber_pagination_negative_page_index(session: Session) -> None:
    collection = SubscriberCollection(session, page=-13)
    assert collection.page == 0
    assert collection.page_index == 0
    assert collection.page_by_index(-4).page == 0
    assert collection.page_by_index(-5).page_index == 0

    with pytest.raises(AssertionError):
        SubscriberCollection(session, page=None)  # type: ignore[arg-type]


def test_subscriber_collection_term(session: Session) -> None:
    collection: SubscriberCollection[Any]
    # Add email subscribers
    collection = EmailSubscriberCollection(session)
    for number in range(100):
        collection.add(
            'user{:02}@example.org'.format(number),
            None,
            None,
            'de_CH',
            active=True
        )
    assert collection.query().count() == 100

    # Add SMS subscribers
    collection = SmsSubscriberCollection(session)
    for number in range(100):
        collection.add(
            '+417911122{:02}'.format(number),
            None,
            None,
            'de_CH',
            active=True
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


def test_subscriber_collection_export(session: Session) -> None:
    # Add email subscribers
    emails = EmailSubscriberCollection(session, active_only=False)
    emails.add('a@example.org', None, None, 'de_CH', True)
    emails.add('b@example.org', 'canton', None, 'de_CH', False)
    emails.add('c@example.org', 'municipality', 'Govikon', 'fr_CH', True)

    # Add SMS subscribers
    sms = SmsSubscriberCollection(session, active_only=False)
    sms.add('+41791112201', None, None, 'de_CH', True)
    sms.add('+41791112202', 'canton', None, 'fr_CH', False)
    sms.add('+41791112203', 'municipality', 'Govikon', 'fr_CH', True)

    mixed = SubscriberCollection(session, active_only=False)
    assert mixed.query().count() == 6

    # Test email export
    data = emails.export()
    assert sorted(data, key=lambda x: x['address']) == [
        {'active': True, 'address': 'a@example.org', 'domain': None,
         'domain_segment': None, 'locale': 'de_CH',
         'active_since': None, 'inactive_since': None},
        {'active': False, 'address': 'b@example.org', 'domain': 'canton',
         'domain_segment': None, 'locale': 'de_CH',
         'active_since': None, 'inactive_since': None},
        {'active': True, 'address': 'c@example.org', 'domain': 'municipality',
         'domain_segment': 'Govikon', 'locale': 'fr_CH',
         'active_since': None, 'inactive_since': None},
    ]

    # Test SMS export
    data = sms.export()
    assert sorted(data, key=lambda x: x['address']) == [
        {'active': True, 'address': '+41791112201', 'domain': None,
         'domain_segment': None, 'locale': 'de_CH',
         'active_since': None, 'inactive_since': None},
        {'active': False, 'address': '+41791112202', 'domain': 'canton',
         'domain_segment': None, 'locale': 'fr_CH',
         'active_since': None, 'inactive_since': None},
        {'active': True, 'address': '+41791112203', 'domain': 'municipality',
         'domain_segment': 'Govikon', 'locale': 'fr_CH',
         'active_since': None, 'inactive_since': None},
    ]

    # Test mixed export
    data = mixed.export()
    assert sorted(data, key=lambda x: x['address']) == [
        {'active': True, 'address': '+41791112201', 'domain': None,
         'domain_segment': None, 'locale': 'de_CH',
         'active_since': None, 'inactive_since': None},
        {'active': False, 'address': '+41791112202', 'domain': 'canton',
         'domain_segment': None, 'locale': 'fr_CH',
         'active_since': None, 'inactive_since': None},
        {'active': True, 'address': '+41791112203', 'domain': 'municipality',
         'domain_segment': 'Govikon', 'locale': 'fr_CH',
         'active_since': None, 'inactive_since': None},
        {'active': True, 'address': 'a@example.org', 'domain': None,
         'domain_segment': None, 'locale': 'de_CH',
         'active_since': None, 'inactive_since': None},
        {'active': False, 'address': 'b@example.org', 'domain': 'canton',
         'domain_segment': None, 'locale': 'de_CH',
         'active_since': None, 'inactive_since': None},
        {'active': True, 'address': 'c@example.org', 'domain': 'municipality',
         'domain_segment': 'Govikon', 'locale': 'fr_CH',
         'active_since': None, 'inactive_since': None},
    ]


def test_subscriber_collection_cleanup(session: Session) -> None:
    collection: SubscriberCollection[Any]
    # Add email subscribers
    collection = EmailSubscriberCollection(session)
    collection.add('a@example.org', None, None, 'de_CH', True)
    collection.add('a@example.org', 'canton', None, 'de_CH', True)
    collection.add('b@EXAMPLE.org', None, None, 'de_CH', True)
    collection.add('c@example.org', None, None, 'fr_CH', True)
    collection.add('d@example.org', None, None, 'de_CH', True)

    # Add SMS subscribers
    collection = SmsSubscriberCollection(session)
    collection.add('+41791112201', None, None, 'de_CH', True)
    collection.add('+41791112201', 'canton', None, 'fr_CH', True)
    collection.add('+41791112202', None, None, 'fr_CH', True)
    collection.add('+41791112203', None, None, 'fr_CH', True)

    assert SubscriberCollection(session).query().count() == 9

    # Test deactivate email subscribers
    collection = EmailSubscriberCollection(session)

    errors, count = collection.cleanup(
        BytesIO(''.encode('utf-8')),
        'text/plain',
        delete=False
    )
    assert errors

    csv = (
        'address,\n'
        'a@EXAMPLE.org,\n'
        'b@example.org,\n'
        'c@example.org,\n'
        'e@example.org,\n'
        '123,\n'
        ',\n'
    )

    errors, count = collection.cleanup(
        BytesIO(csv.encode('utf-8')),
        'text/plain',
        delete=False
    )
    assert not errors
    assert count == 4
    assert collection.query().count() == 1
    assert collection.query(active_only=False).count() == 5

    # Test delete email subscribers
    errors, count = collection.cleanup(
        BytesIO(csv.encode('utf-8')),
        'text/plain',
        delete=True
    )
    assert not errors
    assert count == 4
    assert collection.query().count() == 1
    assert collection.query(active_only=False).count() == 1

    # Test deactivate SMS subscribers
    collection = SmsSubscriberCollection(session)

    errors, count = collection.cleanup(
        BytesIO(''.encode('utf-8')),
        'text/plain',
        delete=False
    )
    assert errors

    csv = (
        'address,\n'
        '+41791112201,\n'
        '+41791112203,\n'
        '+41791112220,\n'
        '123,\n'
        ',\n'
    )

    errors, count = collection.cleanup(
        BytesIO(csv.encode('utf-8')),
        'text/plain',
        delete=False
    )
    assert not errors
    assert count == 3
    assert collection.query().count() == 1
    assert collection.query(active_only=False).count() == 4

    # Test delete SMS subscribers
    errors, count = collection.cleanup(
        BytesIO(csv.encode('utf-8')),
        'text/plain',
        delete=True
    )
    assert not errors
    assert count == 3
    assert collection.query().count() == 1
    assert collection.query(active_only=False).count() == 1
