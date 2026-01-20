from __future__ import annotations

from onegov.chat import Message
from onegov.chat import MessageCollection
from onegov.core.custom import json
from onegov.core.security import Private
from onegov.core.templates import render_template
from onegov.file import File
from onegov.file.models.file_message import FileMessage
from onegov.org import OrgApp, _
from onegov.org.layout import MessageCollectionLayout
from onegov.user import User
from sqlalchemy import inspect


from typing import NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSONObject_ro, RenderData
    from onegov.org.request import OrgRequest


# messages rendered by this view need to provide a 'message_[type].pt'
# template and they should provide a link method that takes a
# request and returns the link the message points (the subject of the message)
#
# for messages which are created outside onegov.org and descendants, the links
# might have to be implemented in link_message below
def render_message(
    message: Message,
    request: OrgRequest,
    owner: Owner,
    layout: MessageCollectionLayout,
) -> str:
    return render_template(
        template=f'message_{message.type}',
        request=request,
        content={
            'layout': layout,
            'model': message,
            'owner': owner,
            'link': link_message(message, request),
        },
        suppress_global_variables=True
    )


def link_message(message: Message, request: OrgRequest) -> str:
    if hasattr(message, 'link'):
        return message.link(request)

    if isinstance(message, FileMessage):
        return request.class_link(File, {
            'id': message.channel_id
        })

    raise NotImplementedError


class Owner(NamedTuple):
    username: str
    realname: str | None

    @property
    def initials(self) -> str:
        return User.get_initials(self.username, self.realname)

    @property
    def name(self) -> str:
        return self.realname or self.username


@OrgApp.json(model=MessageCollection, permission=Private, name='feed')
def view_messages_feed(
    self: MessageCollection[Message],
    request: OrgRequest,
    layout: MessageCollectionLayout | None = None
) -> JSONObject_ro:

    mapper = inspect(Message).polymorphic_map
    layout = layout or MessageCollectionLayout(self, request)

    # FIXME: Is this cast actually necessary?
    def cast(message: Message) -> Message:
        message.__class__ = mapper[message.type].class_
        return message

    messages = tuple(cast(m) for m in self.query())
    usernames = {m.owner for m in messages if m.owner}

    hide_personal_email = (request.app.org.hide_personal_email
                  and not request.is_manager)
    hide_submitter_email = (request.app.org.hide_submitter_email
                              and not request.is_manager)
    general = request.app.org.general_email or ''
    submitter_name = request.translate(_('Submitter'))

    if usernames:
        q = request.session.query(User)
        q = q.with_entities(User.username, User.realname)
        q = q.filter(User.username.in_(usernames))

        owners = {u.username: Owner(
            general if hide_personal_email else u.username, u.realname
        ) for u in q}
        owners.update({
            username: Owner(
                submitter_name if hide_submitter_email else username, None)
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
                'subtype': m.subtype or '',
                'date': ', '.join((
                    layout.format_date(m.created, 'weekday_long'),
                    layout.format_date(m.created, 'date_long')
                )),
                'owner': owners[m.owner].username,
                'html': render_message(
                    message=m,
                    request=request,
                    owner=owners[m.owner],
                    layout=layout
                ),
            }
            for m in messages
            # FIXME: Currently it seems like we never have messages without
            #        an owner, but if we ever do, we will crash and burn
            #        either in the template or in this loop, so for now we
            #        skip messages without owner
            if m.owner
        ]
    }


@OrgApp.html(
    model=MessageCollection,
    permission=Private,
    template='timeline.pt'
)
def view_messages(
    self: MessageCollection[Message],
    request: OrgRequest,
    layout: MessageCollectionLayout | None = None
) -> RenderData:

    # The initial load contains only the 25 latest message (the feed will
    # return the 25 oldest messages by default)
    if not self.newer_than:
        beyond_horizon = self.latest_message(offset=25)

        if beyond_horizon:
            self.newer_than = beyond_horizon.id

    return {
        'layout': layout or MessageCollectionLayout(self, request),
        'title': _('Timeline'),
        'feed': request.link(self, 'feed'),
        'feed_data': json.dumps(
            view_messages_feed(self, request)
        ),
        'feed_interval': 15
    }
