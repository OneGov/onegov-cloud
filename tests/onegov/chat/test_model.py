from __future__ import annotations

import time

from onegov.chat import Message
from tests.shared.utils import create_image
from onegov.file import File


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_message_edited(session: Session) -> None:
    session.add(Message(text='Yo', channel_id='#public'))
    session.flush()

    message1 = session.query(Message).one()
    assert not message1.edited

    message = session.query(Message).filter(Message.edited == True).first()
    assert message is None

    message = session.query(Message).filter(Message.edited == False).first()
    assert message is not None
    message.text = 'Sup'
    session.flush()

    message = session.query(Message).one()
    assert message.edited

    message = session.query(Message).filter(Message.edited == True).first()
    assert message is not None
    assert message.text == 'Sup'


def test_message_order(session: Session) -> None:

    for i in range(25, 0):
        session.add(Message(text=str(i), channel_id='#public'))
        # the order of messages created within a milisecond of each other
        # are not necessarily ordered correctly (ms is the highest resolution)
        time.sleep(0.001)

    session.flush()

    for ix, message in enumerate(session.query(Message).order_by(Message.id)):
        assert message.text == str(ix)


def test_message_file(session: Session) -> None:
    session.add(Message(
        text='Selfie',
        channel_id='#public',
        file=File(name='selfie.png', reference=create_image(2048, 2048))
    ))

    session.flush()

    message = session.query(Message).one()
    assert message.file
    assert session.query(File).count() == 1

    session.delete(message)
    session.flush()

    assert session.query(File).count() == 0


def test_bound_messages(session: Session) -> None:
    class MyMessage(Message):
        __mapper_args__ = {'polymorphic_identity': 'mymessage'}

    msg1 = Message(text='Hi', channel_id='#public')
    session.add(msg1)
    msg2 = MyMessage(text='Hello', channel_id='#public')
    session.add(msg2)

    assert MyMessage.bound_messages(session).query().all() == [msg2]
    assert Message.bound_messages(session).query().all() == [msg1]
