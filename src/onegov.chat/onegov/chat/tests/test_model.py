import time

from onegov.chat import Message
from onegov_testing.utils import create_image
from onegov.file import File


def test_message_edited(session):
    session.add(Message(text='Yo', channel_id='#public'))
    session.flush()

    message = session.query(Message).one()
    assert not message.edited

    message = session.query(Message).filter(Message.edited == True).first()
    assert message is None

    message = session.query(Message).filter(Message.edited == False).first()
    message.text = 'Sup'
    session.flush()

    message = session.query(Message).one()
    assert message.edited

    message = session.query(Message).filter(Message.edited == True).first()
    assert message.text == 'Sup'


def test_message_order(session):

    for i in range(0, 25):
        session.add(Message(text=str(i), channel_id='#public'))
        # the order of messages created within a milisecond of each other
        # are not necessarily ordered correctly (ms is the highest resolution)
        time.sleep(0.001)

    session.flush()

    for ix, message in enumerate(session.query(Message).order_by(Message.id)):
        assert message.text == str(ix)


def test_message_file(session):
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
