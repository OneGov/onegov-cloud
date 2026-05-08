from __future__ import annotations

from onegov.recipient.collection import GenericRecipientCollection
from onegov.recipient.model import GenericRecipient


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_recipient_model_order(session: Session) -> None:
    session.add(GenericRecipient(
        name="Peter's Url",
        medium="http",
        address="http://example.org/push",
        extra="POST"
    ))
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

    session.flush()

    collection: GenericRecipientCollection[GenericRecipient]
    collection = GenericRecipientCollection(session, type='generic')
    email, phone, url = collection.query().all()
    assert email.order == 'peter-s-cellphone'
    assert phone.order == 'peter-s-e-mail'
    assert url.order == 'peter-s-url'


def test_recipient_collection(session: Session) -> None:

    class FooRecipient(GenericRecipient):
        __mapper_args__ = {'polymorphic_identity': 'foo'}

    class BarRecipient(GenericRecipient):
        __mapper_args__ = {'polymorphic_identity': 'bar'}

    bar_recipients: GenericRecipientCollection[BarRecipient]
    bar_recipients = GenericRecipientCollection(session, type='bar')
    bar_recipients.add(
        name="Hidden recipient",
        medium="phone",
        address="+12 345 67 89"
    )

    foo_recipients: GenericRecipientCollection[FooRecipient]
    foo_recipients = GenericRecipientCollection(session, type='foo')
    foo = foo_recipients.add(
        name="Peter's Cellphone",
        medium="phone",
        address="+12 345 67 89"
    )

    assert foo_recipients.query().count() == 1
    assert bar_recipients.query().count() == 1

    for obj in (foo, foo_recipients.query().one()):
        assert obj.type == 'foo'
        assert isinstance(obj, FooRecipient)

    foo_recipients.delete(foo)
    assert foo_recipients.query().count() == 0
