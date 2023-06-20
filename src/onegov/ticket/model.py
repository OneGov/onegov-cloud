from sqlalchemy.dialects.postgresql import TSVECTOR

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.core.orm.types import UTCDateTime
from onegov.search import ORMSearchable
from onegov.search.utils import create_tsvector_string, adds_fts_column, \
    drops_fts_column
from onegov.ticket import handlers
from onegov.ticket.errors import InvalidStateChange
from onegov.user import User
from onegov.user import UserGroup
from sedate import utcnow
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, Text, \
    Index
from sqlalchemy import Computed  # type:ignore[attr-defined]
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import backref, deferred, relationship
from uuid import uuid4

FTS_TICKET_COL_NAME = 'fts_ticket_idx'


def ticket_tsvector_string():
    """
    index is built on columns title and location as well as the json
    fields description and organizer in content column
    """
    s = create_tsvector_string('number')
    return s


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

    #: the subtitle of the ticket for extra information about it's content
    subtitle = Column(Text, nullable=True)

    #: the group this ticket belongs to. used to differentiate tickets
    #: belonging to one specific handler (handler -> group -> title)
    group = Column(Text, nullable=False)

    #: the name of the handler associated with this ticket, may be used to
    #: create custom polymorphic subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
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

    #: a timestamp recorded every time the state changes
    last_state_change = Column(UTCDateTime, nullable=True)

    #: the time in seconds between the ticket's creation and the time it
    #: got accepted (changed from open to pending)
    reaction_time = Column(Integer, nullable=True)

    #: the time in seconds a ticket was in the pending state -
    #: may be a moving target, so use :attr:`current_process_time` to get the
    #: adjusted process_time based on the current time.
    #: ``process_time`` itself is only accurate if the ticket is closed, so in
    #: reports make sure to account for the ticket state.
    process_time = Column(Integer, nullable=True)

    #: true if the notifications for this ticket should be muted
    muted = Column(Boolean, nullable=False, default=False)

    # column for full text search index
    fts_ticket_idx = Column(TSVECTOR, Computed(
        f"to_tsvector('german', {ticket_tsvector_string()})",
        persisted=True))

    __table_args__ = (
        Index(
            'fts_tickets',
            fts_ticket_idx,
            postgresql_using='gin'
        ),
    )

    # override the created attribute from the timestamp mixin - we don't want
    # it to be deferred by default because we usually need it
    @declared_attr
    def created(cls):
        return Column(UTCDateTime, default=cls.timestamp)

    #: the state of this ticket (open, pending, closed, archived)
    state = Column(
        Enum(
            'open',
            'pending',
            'closed',
            'archived',
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
        'number': {'type': 'text'},
        'title': {'type': 'text'},
        'subtitle': {'type': 'text'},
        'group': {'type': 'text'},
        'ticket_email': {'type': 'keyword'},
        'ticket_data': {'type': 'localized_html'},
        'extra_localized_text': {'type': 'localized'}
    }

    @property
    def extra_localized_text(self):
        """ Maybe used by child-classes to return localized extra data that
        should be indexed as well.

        """
        return None

    @property
    def es_suggestion(self):
        return [
            self.number,
            self.number.replace('-', '')
        ]

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

    @property
    def current_process_time(self):

        if self.state == 'closed':
            return self.process_time

        elif self.state == 'open':
            return int((utcnow() - self.created).total_seconds())

        elif self.state == 'pending':

            # tickets created before the introduction of process time do not
            # have the necessary information to be migrated
            if not self.last_state_change or not self.reaction_time:
                return None

            running_time = (utcnow() - self.last_state_change).total_seconds()
            accrued_process_time = (self.process_time or 0)

            return int(accrued_process_time + running_time)

        else:
            raise NotImplementedError

    def accept_ticket(self, user):

        if self.state == 'pending' and self.user == user:
            return

        if self.state != 'open':
            raise InvalidStateChange()

        self.last_state_change = state_change = self.timestamp()
        self.reaction_time = int((state_change - self.created).total_seconds())
        self.state = 'pending'
        self.user = user

    def close_ticket(self):

        if self.state == 'closed':
            return

        if self.state != 'pending':
            raise InvalidStateChange()

        self.process_time = self.current_process_time
        self.last_state_change = self.timestamp()
        self.state = 'closed'

    def reopen_ticket(self, user):
        if self.state == 'pending' and self.user == user:
            return

        if self.state != 'closed':
            raise InvalidStateChange()

        self.last_state_change = self.timestamp()
        self.state = 'pending'
        self.user = user

    def archive_ticket(self):
        if self.state != 'closed':
            raise InvalidStateChange()

        self.last_state_change = self.timestamp()
        self.state = 'archived'

    def unarchive_ticket(self, user):
        if self.state != 'archived':
            raise InvalidStateChange()
        self.last_state_change = self.timestamp()
        self.state = 'closed'
        self.user = user

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
        for info in ('name', 'address', 'phone'):
            data = getattr(self.handler, f'submitter_{info}')
            if data:
                self.snapshot[f'submitter_{info}'] = data

    @staticmethod
    def reindex(session, schema):
        """
        Re-indexes the table by dropping and adding the full text search
        column.
        """
        Ticket.drop_fts_column(session, schema)
        Ticket.add_fts_column(session, schema)

    @staticmethod
    def add_fts_column(session, schema):
        """
        Adds full text search column to table `events`

        :param session: db session
        :param schema: schema the full text column shall be added
        :return: None
        """
        adds_fts_column(schema, session, Ticket.__tablename__,
                        FTS_TICKET_COL_NAME, ticket_tsvector_string())

    @staticmethod
    def drop_fts_column(session, schema):
        """
        Drops the full text search column

        :param session: db session
        :param schema: schema the full text column shall be added
        :return: None
        """
        drops_fts_column(schema, session, Ticket.__tablename__,
                         FTS_TICKET_COL_NAME)


class TicketPermission(Base, TimestampMixin):
    """ Defines a custom ticket permission.

    If a ticket permission is defined for ticket handler (and optionally a
    group), a user has to be in the given user group to access these tickets.

    """

    __tablename__ = 'ticket_permissions'

    #: the id
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the user group needed for accessing the tickets
    user_group_id = Column(UUID, ForeignKey(UserGroup.id), nullable=False)
    user_group = relationship(
        UserGroup,
        backref=backref(
            'ticket_permissions',
            cascade='all, delete-orphan',
        )
    )

    #: the handler code this permission addresses
    handler_code = Column(Text, nullable=False)

    #: the group this permission addresses
    group = Column(Text, nullable=True)
