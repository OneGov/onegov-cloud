import isodate

from onegov.chat import Message
from onegov.chat import MessageCollection
from onegov.core.security import Private
from onegov.org import OrgApp, _
from onegov.org.layout import MessageCollectionLayout
from sqlalchemy import inspect


@OrgApp.json(model=MessageCollection, permission=Private, name='feed')
def view_messages_feed(self, request):
    mapper = inspect(Message).polymorphic_map

    return {
        'messages': [
            {
                'id': m.id.hex,
                'channel_id': m.channel_id,
                'owner': m.owner,
                'type': m.type,
                'text': mapper[m.type].class_.get(m, request),
                'created': isodate.datetime_isoformat(m.created)
            } for m in self.query()
        ]
    }


@OrgApp.html(
    model=MessageCollection,
    permission=Private,
    template='timeline.pt'
)
def view_messages(self, request):

    return {
        'layout': MessageCollectionLayout(self, request),
        'title': _("Timeline"),
        'feed': request.link(self, 'feed'),
        'poll_interval': 5
    }
