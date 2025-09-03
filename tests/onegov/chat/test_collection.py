from __future__ import annotations

from onegov.chat import MessageCollection
from time import sleep


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_collection_filter(session: Session) -> None:
    msgs = MessageCollection(session)
    msgs.add(channel_id='public', text='Yo!')
    msgs.add(channel_id='public', text='Yo Sup?')
    msgs.add(channel_id='public', text='Sup?')
    msgs.add(channel_id='private', text='U female?')

    public = MessageCollection(session, channel_id='public')
    all_public = public.query().all()
    assert len(all_public) == 3
    assert all_public == sorted(all_public, key=lambda m: m.id)

    private = MessageCollection(session, channel_id='private')
    assert private.query().count() == 1

    latest = msgs.latest_message()
    assert latest is not None
    msgs.newer_than = latest.id
    latest = msgs.add(channel_id='private', text='Nope')
    assert msgs.query().count() == 1

    msgs.newer_than = None
    msgs.older_than = latest.id
    assert msgs.query().count() == 4

    msgs.limit = 1
    assert msgs.query().count() == 1


def test_latest_message(session: Session) -> None:
    msgs = MessageCollection(session)
    msg1 = msgs.add(channel_id='public', text='Yo!')
    assert msgs.latest_message() == msg1
    # to ensure we get an ordered ulid for the next message
    sleep(0.001)

    msg2 = msgs.add(channel_id='public', text='Yo Sup?')
    assert msgs.latest_message() == msg2
    sleep(0.001)

    msg3 = msgs.add(channel_id='public', text='Sup?')
    assert msgs.latest_message() == msg3
    sleep(0.001)

    msg4 = msgs.add(channel_id='private', text='U female?')
    assert msgs.latest_message() == msg4
    assert msgs.latest_message(offset=1) == msg3
    assert msgs.latest_message(offset=2) == msg2
    assert msgs.latest_message(offset=3) == msg1
    # it shouldn't care if the offset is past the oldest message
    assert msgs.latest_message(offset=4) is None
    assert msgs.latest_message(offset=5) is None
