from collections import namedtuple
from onegov.chat import Message
from onegov.chat import MessageCollection
from onegov.core.custom import json
from onegov.core.security import Private
from onegov.org import OrgApp, _
from onegov.org.layout import MessageCollectionLayout
from onegov.user import User
from sqlalchemy import inspect


class Owner(namedtuple('OwnerBase', ('username', 'realname'))):

    @property
    def initials(self):
        return User.get_initials(self.username, self.realname)

    @property
    def name(self):
        return self.realname or self.username


@OrgApp.json(model=MessageCollection, permission=Private, name='feed')
def view_messages_feed(self, request):
    mapper = inspect(Message).polymorphic_map
    layout = MessageCollectionLayout(self, request)

    def cast(message):
        message.__class__ = mapper[message.type].class_
        return message

    messages = tuple(cast(m) for m in self.query())
    usernames = {m.owner for m in messages if m.owner}

    if usernames:
        q = request.session.query(User)
        q = q.with_entities(User.username, User.realname)
        q = q.filter(User.username.in_(usernames))

        owners = {u.username: Owner(u.username, u.realname) for u in q}
        owners.update({
            username: Owner(username, None)
            for username in usernames
            if username not in owners
        })
    else:
        owners = {}

    return {
        'messages': [
            {
                'id': m.id,
                'type': m.type,
                'date': ', '.join((
                    layout.format_date(m.created, 'weekday_long'),
                    layout.format_date(m.created, 'date_long')
                )),
                'html': m.get(
                    request,
                    owner=owners.get(m.owner),
                    layout=layout
                ),
            } for m in messages
        ]
    }


@OrgApp.html(
    model=MessageCollection,
    permission=Private,
    template='timeline.pt'
)
def view_messages(self, request):

    # The initial load contains only the 25 latest message (the feed will
    # return the 25 oldest messages by default)
    if not self.newer_than:
        beyond_horizon = self.latest_message(offset=25)

        if beyond_horizon:
            self.newer_than = beyond_horizon.id

    return {
        'layout': MessageCollectionLayout(self, request),
        'title': _("Timeline"),
        'feed': request.link(self, 'feed'),
        'feed_data': json.dumps(
            view_messages_feed(self, request)
        ),
        'feed_interval': 15
    }
