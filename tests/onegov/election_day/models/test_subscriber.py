from onegov.election_day.models import EmailSubscriber
from onegov.election_day.models import SmsSubscriber
from onegov.election_day.models import Subscriber


def test_subscriber(session):
    session.add(Subscriber(address='endpoint', locale='de_CH'))
    session.add(EmailSubscriber(address='end@poi.nt', locale='fr_CH'))
    session.add(SmsSubscriber(address='+41791112233', locale='it_CH'))
    session.flush()

    assert session.query(Subscriber).count() == 3

    subscriber = session.query(EmailSubscriber).one()
    assert subscriber.id
    assert subscriber.address == 'end@poi.nt'
    assert subscriber.locale == 'fr_CH'

    subscriber = session.query(SmsSubscriber).one()
    assert subscriber.id
    assert subscriber.address == '+41791112233'
    assert subscriber.locale == 'it_CH'
