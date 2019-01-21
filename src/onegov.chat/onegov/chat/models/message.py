import sedate

from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.types import JSON, UTCDateTime
from onegov.file import File
from sqlalchemy import Column, Text
from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property
from ulid import ulid


class MessageFile(File):
    __mapper_args__ = {'polymorphic_identity': 'messagefile'}


class Message(Base):
    """ A single chat message bound to channel. """

    __tablename__ = 'messages'

    #: the public id of the message - uses ulid for absolute ordering
    id = Column(Text, primary_key=True, default=ulid)

    #: channel to which this message belongs -> this might one day be
    #: linked to an actual channel record - for now it's just a string that
    #: binds all messages with the same string together
    channel_id = Column(Text, index=True, nullable=False)

    #: optional owner of the message -> this is just an identifier, it isn't
    #: necessarily linked to the user table
    owner = Column(Text, nullable=True)

    #: the polymorphic type of the message
    type = Column(Text, nullable=True)

    #: meta information specific to this message and maybe its type -> we
    #: don't use the meta/content mixin yet as we might not need the content
    #: property
    meta = Column(JSON, nullable=False, default=dict)

    #: the text of the message, maybe None for certain use cases (say if the
    # content of the message is generated from the meta property)
    text = Column(Text, nullable=True)

    #: the time this message was created - not taken from the timestamp mixin
    #: because here we don't want it to be deferred
    created = Column(UTCDateTime, default=sedate.utcnow)

    #: the time this message was modified - not taken from the timestamp mixin
    #: because here we don't want it to be deferred
    modified = Column(UTCDateTime, onupdate=sedate.utcnow)

    #: a single optional file associated with this message
    file = associated(File, 'file', 'one-to-one')

    __mapper_args__ = {
        'order_by': id
    }

    # we need to override __hash__ and __eq__ to establish the equivalence of
    # polymorphic subclasses that differ - we need to compare the base class
    # with subclasses to work around a limitation of the association proxy
    # (see backref in onegov.core.orm.abstract.associable.associated)
    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        if isinstance(other, self.__class__) \
                and self.id == other.id\
                and self.channel_id == other.channel_id:

            return True

        return super().__eq__(other)

    def get(self, request):
        """ Code rendering a message should call this method to get the
        actual text of the message. It might be rendered from meta or it
        might be returned directly from the text column.

        How this is done is up to the polymorphic Message.

        """
        return self.text

    @hybrid_property
    def edited(self):
        # use != instead of "is not" as we want this translated into SQL
        return self.modified != None

    @classmethod
    def bound_messages(cls, session):
        """ A message collection bound to the polymorphic identity of this
        message.

        """
        from onegov.chat import MessageCollection  # XXX circular import

        return MessageCollection(
            session=session,
            type=cls.__mapper_args__['polymorphic_identity']
        )


@event.listens_for(Message, 'init')
def init(target, args, kwargs):
    """ Ensures that the message id is created upon instantiation. This helps
    to ensure that each message is ordered according to it's creation.

    Note that messages created within a millisecond of each other are ordered
    randomly.

    """
    target.id = ulid()
