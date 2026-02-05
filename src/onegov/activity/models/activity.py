from __future__ import annotations

from onegov.activity.models.occasion import Occasion
from onegov.activity.models.period import BookingPeriod
from onegov.activity.utils import extract_thumbnail, extract_municipality
from onegov.core.orm import Base, observes
from onegov.core.orm.mixins import (
    dict_markup_property,
    ContentMixin,
    meta_property,
    TimestampMixin,
)
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from onegov.user import User
from sqlalchemy import Column, Enum, Text, ForeignKey
from sqlalchemy import exists, and_
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import object_session, relationship
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterable
    from onegov.activity.collections import PublicationRequestCollection
    from onegov.activity.models import BookingPeriodMeta, PublicationRequest
    from onegov.core.orm.mixins import dict_property
    from typing import Literal
    from typing import Self, TypeAlias

    ActivityState: TypeAlias = Literal[
        'preview',
        'proposed',
        'accepted',
        'archived'
    ]


# Note, a database migration is needed if these states are changed
ACTIVITY_STATES: tuple[ActivityState, ...] = (
    'preview',
    'proposed',
    'accepted',
    'archived'
)


class Activity(Base, ContentMixin, TimestampMixin):
    """ Describes an activity that is made available to participants on
    certain occasions (i.e. dates).

    The activity describes the what's going on, the occasion describes when
    and with whom.

    """

    __tablename__ = 'activities'

    #: An internal id for references (not public)
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: A nice id for the url, readable by humans
    name: Column[str] = Column(Text, nullable=False, unique=True)

    #: The title of the activity
    title: Column[str] = Column(Text, nullable=False)

    #: The normalized title for sorting
    order: Column[str] = Column(Text, nullable=False, index=True)

    #: Describes the activity briefly
    lead: dict_property[str | None] = meta_property()

    #: Describes the activity in detail
    text = dict_markup_property('content')

    #: The thumbnail shown in the overview
    thumbnail: dict_property[str | None] = meta_property()

    #: Tags/Categories of the activity
    _tags: Column[dict[str, str] | None] = Column(  # type:ignore
        MutableDict.as_mutable(HSTORE),  # type:ignore[no-untyped-call]
        nullable=True,
        name='tags'
    )

    #: The user to which this activity belongs to (organiser)
    username: Column[str] = Column(
        Text,
        ForeignKey(User.username),
        nullable=False
    )

    #: The user which initially reported this activity (same as username, but
    #: this value may not change after initialisation)
    reporter: Column[str] = Column(Text, nullable=False)

    #: Describes the location of the activity
    location: Column[str | None] = Column(Text, nullable=True)

    #: The municipality in which the activity is held, from the location
    municipality: Column[str | None] = Column(Text, nullable=True)

    #: Access the user linked to this activity
    user: relationship[User] = relationship(User)

    #: The occasions linked to this activity
    occasions: relationship[list[Occasion]] = relationship(
        Occasion,
        order_by='Occasion.order',
        back_populates='activity'
    )

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    #: the state of the activity
    state: Column[ActivityState] = Column(
        Enum(*ACTIVITY_STATES, name='activity_state'),  # type:ignore[arg-type]
        nullable=False,
        default='preview'
    )

    #: The publication requests linked to this activity
    publication_requests: relationship[list[PublicationRequest]] = (
        relationship(
            'PublicationRequest',
            back_populates='activity'
        )
    )

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic',
    }

    @observes('title')
    def title_observer(self, title: str) -> None:
        self.order = normalize_for_url(title)

    @observes('username')
    def username_observer(self, username: str) -> None:
        if not self.reporter:
            self.reporter = username

    @observes('content')
    def content_observer(self, content: dict[str, Any] | None) -> None:
        self.thumbnail = extract_thumbnail(self.content.get('text'))

    @observes('location')
    def location_observer(self, content: str | None) -> None:
        municipality = extract_municipality(self.location)

        if municipality:
            self.municipality = municipality[1]
        else:
            self.municipality = None

    @property
    def tags(self) -> set[str]:
        return set(self._tags.keys()) if self._tags else set()

    @tags.setter
    def tags(self, value: Iterable[str]) -> None:
        self._tags = dict.fromkeys(value, '') if value else None

    @property
    def active_occasions(self) -> list[Occasion]:
        """ Returns the list of active occasions for this activity. An occasion
        is active if its period is the currently active period.
        """
        session = object_session(self)
        active_periods = session.query(BookingPeriod.id).filter_by(active=True)
        return [
            occasion for occasion in self.occasions
            if occasion.period_id in (pid for (pid,) in active_periods)
        ]

    def propose(self) -> Self:
        assert self.state in ('preview', 'proposed')
        self.state = 'proposed'

        return self

    def accept(self) -> Self:
        self.state = 'accepted'

        return self

    def archive(self) -> Self:
        self.state = 'archived'

        return self

    def create_publication_request(
        self,
        period: BookingPeriod,
        **kwargs: Any  # TODO: better type safety
    ) -> PublicationRequest:
        return self.requests.add(activity=self, period=period, **kwargs)

    @property
    def requests(self) -> PublicationRequestCollection:
        # XXX circular imports
        from onegov.activity.collections.publication_request import (
            PublicationRequestCollection)

        return PublicationRequestCollection(object_session(self))

    @property
    def latest_request(self) -> PublicationRequest | None:
        q = self.requests.query()
        q = q.filter_by(activity_id=self.id)
        q = q.join(BookingPeriod)
        q = q.order_by(
            BookingPeriod.active.desc(),
            BookingPeriod.execution_start.desc()
        )

        return q.first()

    def request_by_period(
        self,
        period: BookingPeriod | BookingPeriodMeta | None
    ) -> PublicationRequest | None:

        if not period:
            return None
        q = self.requests.query()
        q = q.filter_by(activity_id=self.id, period_id=period.id)

        return q.first()

    def has_occasion_in_period(
        self,
        period: BookingPeriod | BookingPeriodMeta
    ) -> bool:
        q = object_session(self).query(
            exists().where(and_(
                Occasion.activity_id == self.id,
                Occasion.period_id == period.id
            ))
        )

        return q.scalar()
