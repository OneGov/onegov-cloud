from __future__ import annotations

from onegov.activity.models.occasion import Occasion
from onegov.activity.models.period import BookingPeriod
from onegov.activity.utils import extract_thumbnail, extract_municipality
from onegov.core.orm import Base, observes
from onegov.core.orm.mixins import (
    dict_property,
    dict_markup_property,
    meta_property,
    ContentMixin,
    TimestampMixin,
)
from onegov.core.utils import normalize_for_url
from onegov.user import User
from sqlalchemy import Enum, ForeignKey
from sqlalchemy import exists, and_
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import mapped_column, object_session, relationship, Mapped
from uuid import uuid4, UUID


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.activity.collections import PublicationRequestCollection
    from onegov.activity.models import BookingPeriodMeta, PublicationRequest
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
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: A nice id for the url, readable by humans
    name: Mapped[str] = mapped_column(unique=True)

    #: The title of the activity
    title: Mapped[str]

    #: The normalized title for sorting
    order: Mapped[str] = mapped_column(index=True)

    #: Describes the activity briefly
    lead: dict_property[str | None] = meta_property()

    #: Describes the activity in detail
    text = dict_markup_property('content')

    #: The thumbnail shown in the overview
    thumbnail: dict_property[str | None] = meta_property()

    #: Tags/Categories of the activity
    _tags: Mapped[dict[str, str] | None] = mapped_column(
        MutableDict.as_mutable(HSTORE),
        name='tags'
    )

    #: The user to which this activity belongs to (organiser)
    username: Mapped[str] = mapped_column(ForeignKey(User.username))

    #: The user which initially reported this activity (same as username, but
    #: this value may not change after initialisation)
    reporter: Mapped[str]

    #: Describes the location of the activity
    location: Mapped[str | None]

    #: The municipality in which the activity is held, from the location
    municipality: Mapped[str | None]

    #: Access the user linked to this activity
    user: Mapped[User] = relationship()

    #: The occasions linked to this activity
    occasions: Mapped[list[Occasion]] = relationship(
        order_by='Occasion.order',
        back_populates='activity'
    )

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    #: the state of the activity
    state: Mapped[ActivityState] = mapped_column(
        Enum(*ACTIVITY_STATES, name='activity_state'),
        default='preview'
    )

    #: The publication requests linked to this activity
    publication_requests: Mapped[list[PublicationRequest]] = relationship(
        back_populates='activity'
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
        assert session is not None
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

        session = object_session(self)
        assert session is not None
        return PublicationRequestCollection(session)

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
        session = object_session(self)
        assert session is not None
        q = session.query(
            exists().where(and_(
                Occasion.activity_id == self.id,
                Occasion.period_id == period.id
            ))
        )

        return q.scalar()
