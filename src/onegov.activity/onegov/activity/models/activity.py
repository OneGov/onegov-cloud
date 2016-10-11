from onegov.activity.models.occasion import Occasion
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
from sqlalchemy import Column, Enum, Text, ForeignKey, Integer
from sqlalchemy import func, distinct
from sqlalchemy.dialects.postgresql import HSTORE, ARRAY, INT4RANGE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from sqlalchemy_utils import aggregated, observes
from uuid import uuid4


# Note, a database migration is needed if these states are changed
ACTIVITY_STATES = ('preview', 'proposed', 'accepted', 'denied', 'archived')


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
    lead = meta_property('lead')

    #: Describes the activity in detail
    text = content_property('text')

    #: Tags/Categories of the activity
    _tags = Column(MutableDict.as_mutable(HSTORE), nullable=True, name='tags')

    #: The user to which this activity belongs to (organiser)
    username = Column(Text, ForeignKey(User.username), nullable=False)

    #: The user which initially reported this activity (same as username, but
    #: this value may not change after initialisation)
    reporter = Column(Text, nullable=False)

    #: Access the user linked to this activity
    user = relationship('User')

    @aggregated('occasions', Column(Integer, default=0))
    def durations(self):
        return func.sum(distinct(Occasion.duration))

    @aggregated('occasions', Column(ARRAY(INT4RANGE), default=list))
    def ages(self):
        return func.array_agg(distinct(Occasion.age))

    #: The occasions linked to this activity
    occasions = relationship(
        'Occasion',
        order_by='Occasion.start',
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

    @property
    def tags(self):
        return set(self._tags.keys()) if self._tags else set()

    @tags.setter
    def tags(self, value):
        self._tags = {k: '' for k in value} if value else None

    def propose(self):
        assert self.state == 'preview'
        self.state = 'proposed'

        return self

    def accept(self):
        assert self.state == 'proposed'
        self.state = 'accepted'

        return self

    def deny(self):
        assert self.state == 'proposed'
        self.state = 'denied'

        return self

    def archive(self):
        assert self.state == 'accepted'
        self.state = 'archived'

        return self
