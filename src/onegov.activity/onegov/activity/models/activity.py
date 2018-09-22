from onegov.activity.models.occasion import Occasion
from onegov.activity.models.period import Period
from onegov.activity.utils import extract_thumbnail, extract_municipality
from onegov.core.orm import Base
from onegov.core.orm.mixins import (
    content_property,
    ContentMixin,
    meta_property,
    TimestampMixin,
)
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from onegov.user import User
from sqlalchemy import Column, Enum, Text, ForeignKey
from sqlalchemy import event
from sqlalchemy import exists, and_, desc
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import object_session, relationship
from sqlalchemy_utils import observes
from uuid import uuid4


# Note, a database migration is needed if these states are changed
ACTIVITY_STATES = ('preview', 'proposed', 'accepted', 'archived')


class Activity(Base, ContentMixin, TimestampMixin):
    """ Describes an activity that is made available to participants on
    certain occasions (i.e. dates).

    The activity describes the what's going on, the occasion describes when
    and with whom.

    """

    __tablename__ = 'activities'

    #: An internal id for references (not public)
    id = Column(UUID, primary_key=True, default=uuid4)

    #: A nice id for the url, readable by humans
    name = Column(Text, nullable=False, unique=True)

    #: The title of the activity
    title = Column(Text, nullable=False)

    #: The normalized title for sorting
    order = Column(Text, nullable=False, index=True)

    #: Describes the activity briefly
    lead = meta_property()

    #: Describes the activity in detail
    text = content_property()

    #: The thumbnail shown in the overview
    thumbnail = meta_property()

    #: Tags/Categories of the activity
    _tags = Column(MutableDict.as_mutable(HSTORE), nullable=True, name='tags')

    #: The user to which this activity belongs to (organiser)
    username = Column(Text, ForeignKey(User.username), nullable=False)

    #: The user which initially reported this activity (same as username, but
    #: this value may not change after initialisation)
    reporter = Column(Text, nullable=False)

    #: Describes the location of the activity
    location = Column(Text, nullable=True)

    #: The municipality in which the activity is held, from the location
    municipality = Column(Text, nullable=True)

    #: Access the user linked to this activity
    user = relationship('User')

    #: The occasions linked to this activity
    occasions = relationship(
        'Occasion',
        order_by='Occasion.order',
        backref='activity'
    )

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    #: the state of the activity
    state = Column(
        Enum(*ACTIVITY_STATES, name='activity_state'),
        nullable=False,
        default='preview'
    )

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'order_by': order,
    }

    @observes('title')
    def title_observer(self, title):
        self.order = normalize_for_url(title)

    @observes('username')
    def username_observer(self, username):
        if not self.reporter:
            self.reporter = username

    @observes('content')
    def content_observer(self, content):
        self.thumbnail = extract_thumbnail(self.content.get('text'))

    @observes('location')
    def location_observer(self, content):
        municipality = extract_municipality(self.location)

        if municipality:
            self.municipality = municipality[1]
        else:
            self.municipality = None

    @property
    def tags(self):
        return set(self._tags.keys()) if self._tags else set()

    @tags.setter
    def tags(self, value):
        self._tags = {k: '' for k in value} if value else None

    def propose(self):
        assert self.state in ('preview', 'proposed')
        self.state = 'proposed'

        return self

    def accept(self):
        self.state = 'accepted'

        return self

    def archive(self):
        self.state = 'archived'

        return self

    def create_publication_request(self, period, **kwargs):
        return self.requests.add(activity=self, period=period, **kwargs)

    @property
    def requests(self):
        # XXX circular imports
        from onegov.activity.collections.publication_request import \
            PublicationRequestCollection

        return PublicationRequestCollection(object_session(self))

    @property
    def latest_request(self):
        q = self.requests.query()
        q = q.filter_by(activity_id=self.id)
        q = q.join(Period)
        q = q.order_by(desc(Period.active), desc(Period.execution_start))

        return q.first()

    def request_by_period(self, period):
        q = self.requests.query()
        q = q.filter_by(activity_id=self.id, period_id=period.id)

        return q.first()

    def has_occasion_in_period(self, period):
        q = object_session(self).query(
            exists().where(and_(
                Occasion.activity_id == self.id,
                Occasion.period_id == period.id
            ))
        )

        return q.scalar()


@event.listens_for(Activity.__table__, 'after_create')
def receive_after_create(target, connection, **kw):
    # we need as specialised aggregate function for the active_days column
    # usually we wouldn't create our query using format, but sqlalchemy is
    # not able to correctly create this statement and the schema is not
    # user defined (and if it is, it's ensured to only have safe characters)
    connection.execute(
        'CREATE AGGREGATE "{}".array_cat_agg(anyarray) '
        '(SFUNC=array_cat, STYPE=anyarray)'.format(
            connection._execution_options['schema']
        )
    )
