from onegov.chat import Message


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
