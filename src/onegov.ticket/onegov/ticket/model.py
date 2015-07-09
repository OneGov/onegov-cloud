from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.user.model import User
from sqlalchemy import Column, Enum, ForeignKey, Text


class Ticket(Base, TimestampMixin):
    """ Defines a ticket. """

    __tablename__ = 'tickets'

    #: the internal number of the ticket -> may be used as an access key
    #: for anonymous users
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the unique ticket number known to the end-user -> do *not* use this to
    #: access the ticket as an anonymous user, the number is unique, but it's
    #: not unguessable!
    number = Column(Text, unique=True, nullable=False)

    #: the title of the ticket
    title = Column(Text, nullable=False)

    #: the group this ticket belongs to. used to differentiate tickets
    #: belonging to one specific handler (handler -> group -> title)
    group = Column(Text, nullable=False)

    #: the name of the handler associated with this ticket, may be used to
    #: create custom polymorphic subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    handler = Column(Text, nullable=False)

    #: the data associated with the handler
    handler_data = Column(JSON, nullable=False, default=dict)

    #: the state of this ticket (open, pending, closed)
    state = Column(
        Enum(
            'open',
            'pending',
            'closed',
            name='ticket_state'
        ),
        nullable=False,
        default='open'
    )

    #: the user that owns this ticket with this ticket (optional)
    user_id = Column(UUID, ForeignKey(User.id), nullable=True)

    __mapper_args__ = {
        'polymorphic_on': handler
    }
