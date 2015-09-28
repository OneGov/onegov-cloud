from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.core.orm.types import UTCDateTime
from onegov.search import ORMSearchable
from onegov.ticket import handlers
from onegov.user.model import User
from sqlalchemy import Column, Enum, ForeignKey, Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred, relationship
from uuid import uuid4


class Ticket(Base, TimestampMixin, ORMSearchable):
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
    handler_code = Column(Text, nullable=False, index=True)

    #: a unique id for the handler record
    handler_id = Column(Text, nullable=False, index=True, unique=True)

    #: the data associated with the handler, not meant to be loaded in a list,
    #: therefore deferred.
    handler_data = deferred(Column(JSON, nullable=False, default=dict))

    #: a snapshot of the ticket containing the last summary that made any sense
    #: use this before deleting the model behind a ticket, lest your ticket
    #: becomes nothing more than a number.
    snapshot = deferred(Column(JSON, nullable=False, default=dict))

    # override the created attribute from the timestamp mixin - we don't want
    # it to be deferred by default because we usually need it
    @declared_attr
    def created(cls):
        return Column(UTCDateTime, default=cls.timestamp)

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
    user = relationship(User, backref="tickets")

    __mapper_args__ = {
        'polymorphic_on': handler_code
    }

    # limit the search to the ticket number -> the rest can be found
    es_public = False
    es_properties = {
        'number': {'type': 'string'},
        'title': {'type': 'string'},
        'group': {'type': 'string'},
        'ticket_email': {'type': 'string', 'index': 'not_analyzed'},
        'ticket_data': {'type': 'localized_html'}
    }

    @property
    def es_suggestion(self):
        return [
            self.number,
            self.number.replace('-', '')
        ]

    @property
    def es_language(self):
        return 'de'  # XXX add to database in the future

    @property
    def ticket_email(self):
        if self.handler.deleted:
            return self.snapshot.get('email')
        else:
            return self.handler.email

    @property
    def ticket_data(self):
        if self.handler.deleted:
            return self.snapshot.get('summary')
        else:
            return self.handler.extra_data

    @property
    def handler(self):
        """ Returns an instance of the handler associated with this ticket. """

        return handlers.get(self.handler_code)(
            self, self.handler_id, self.handler_data)

    def accept_ticket(self, user):
        assert self.state == 'open'

        self.user = user
        self.state = 'pending'

    def close_ticket(self):
        assert self.state == 'pending'

        self.state = 'closed'

    def reopen_ticket(self, user):
        assert self.state == 'closed'

        self.user = user
        self.state = 'pending'

    def create_snapshot(self, request):
        """ Takes the current handler and stores the output of the summary
        as a snapshot.

        TODO: This doesn't support multiple langauges at this point. The
        language of the user creating the snapshot will be what's stored.

        In the future we might change this by iterating over all supported
        languages and creating the summary for each language.

        """

        self.snapshot['summary'] = self.handler.get_summary(request)
        self.snapshot['email'] = self.handler.email
