from onegov.recipient.collection import GenericRecipientCollection
from onegov.recipient.model import GenericRecipient


def test_recipient_model_order(session):
    session.add(GenericRecipient(
        name="Peter's Cellphone",
        medium="phone",
        address="+12 345 67 89"
    ))

    session.add(GenericRecipient(
        name="Peter's E-Mail",
        medium="email",
        address="peter@example.org"
    ))

    session.add(GenericRecipient(
        name="Peter's Url",
        medium="http",
        address="http://example.org/push",
        extra="POST"
    ))

    session.flush()

    email, phone, url = session.query(GenericRecipient).all()
    assert email.order == 'peter-s-cellphone'
    assert phone.order == 'peter-s-e-mail'
    assert url.order == 'peter-s-url'


def test_recipient_collection(session):

    class FooRecipient(GenericRecipient):
        __mapper_args__ = {'polymorphic_identity': 'foo'}

    recipients = GenericRecipientCollection(session, type='foo')

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
