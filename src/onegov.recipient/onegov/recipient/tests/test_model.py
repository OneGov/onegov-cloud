from onegov.recipient.collection import RecipientCollection
from onegov.recipient.model import Recipient


def test_recipient_model_order(session):
    session.add(Recipient(
        name="Peter's Cellphone",
        medium="phone",
        address="+12 345 67 89"
    ))

    session.add(Recipient(
        name="Peter's E-Mail",
        medium="email",
        address="peter@example.org"
    ))

    session.add(Recipient(
        name="Peter's Url",
        medium="http",
        address="http://example.org/push",
        extra="POST"
    ))

    session.flush()

    email, phone, url = session.query(Recipient).all()
    assert email.order == 'peters-cellphone'
    assert phone.order == 'peters-e-mail'
    assert url.order == 'peters-url'


def test_recipient_collection(session):

    class FooRecipient(Recipient):
        __mapper_args__ = {'polymorphic_identity': 'foo'}

    recipients = RecipientCollection(session, type='foo')

    foo = recipients.add(
        name="Peter's Cellphone",
        medium="phone",
        address="+12 345 67 89"
    )

    for obj in (foo, recipients.query().first()):
        assert obj.type == 'foo'
        assert isinstance(obj, FooRecipient)

    recipients.delete(foo)
    assert recipients.query().count() == 0
