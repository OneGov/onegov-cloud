from onegov.chat.models import Message
from onegov.core.collection import GenericCollection
from sqlalchemy import desc


class MessageCollection(GenericCollection):

    def __init__(self, session, type='*', channel_id='*', newer_than=None,
                 older_than=None, limit=None):
        super().__init__(session)
        self.type = type
        self.channel_id = channel_id
        self.newer_than = newer_than
        self.older_than = older_than
        self.limit = limit

    @property
    def model_class(self):
        return Message.get_polymorphic_class(self.type, Message)

    def add(self, **kwargs):
        if self.type != '*':
            kwargs.setdefault('type', self.type)
        return super().add(**kwargs)

    def query(self):
        q = self.session.query(self.model_class)

        if self.type != '*':
            q = q.filter_by(type=self.type)

        if self.channel_id != '*':
            q = q.filter_by(channel_id=self.channel_id)

        if self.newer_than is not None:
            q = q.filter(self.model_class.id > self.newer_than)

        if self.older_than is not None:
            q = q.filter(self.model_class.id < self.older_than)

        if self.limit is not None:
            q = q.limit(self.limit)

        return q

    def latest_message(self, offset=0):
        q = self.session.query(self.model_class)
        q = q.order_by(desc(self.model_class.id))

        if offset:
            q = q.offset(min(offset, q.count()))

        return q.first()
