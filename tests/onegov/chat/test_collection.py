from onegov.chat import MessageCollection


def test_collection_filter(session):
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

    msgs.newer_than = msgs.latest_message().id
    latest = msgs.add(channel_id='private', text='Nope')
    assert msgs.query().count() == 1

    msgs.newer_than = None
    msgs.older_than = latest.id
    assert msgs.query().count() == 4

    msgs.limit = 1
    assert msgs.query().count() == 1
