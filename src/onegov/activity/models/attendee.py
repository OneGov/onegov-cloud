from __future__ import annotations

from datetime import date
from onegov.activity.models.booking import Booking
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.crypto import random_token
from onegov.search import ORMSearchable
from sqlalchemy import case, cast, func, select, and_, type_coerce
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import relationship, validates
from translationstring import TranslationString
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Callable
    from onegov.user import User
    from sqlalchemy.sql import ColumnElement
    from typing import overload, Protocol, TypeVar
    from typing_extensions import ParamSpec

    P = ParamSpec('P')
    T = TypeVar('T')

    # FIXME: We should no longer need this once we upgrade to SQLAlchemy 2.0
    class _HybridMethod(Protocol[P, T]):
        @overload
        def __get__(
            self,
            obj: None,
            owner: type[object]
        ) -> Callable[P, ColumnElement[T]]: ...

        @overload
        def __get__(
            self,
            obj: object,
            owner: type[object]
        ) -> Callable[P, T]: ...


class Attendee(Base, TimestampMixin, ORMSearchable):
    """ Attendees are linked to zero to many bookings. Each booking
    has an attendee.

    Though an attendee may be the same person as a username in reality, in the
    model we treat those subjects as separate.

    """

    __tablename__ = 'attendees'

    # HACK: We don't want to set up translations in this module for this single
    #       string, we know we already have a translation in a different domain
    #       so we just manually specify it for now.
    fts_type_title = TranslationString('Attendees', domain='onegov.feriennet')
    fts_properties = {
        'username': {'type': 'text', 'weight': 'A'},
        'name': {'type': 'text', 'weight': 'A'},
        'notes': {'type': 'localized', 'weight': 'C'}
    }
    fts_public = False

    @property
    def fts_suggestion(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.id)

    #: the public id of the attendee
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the user owning the attendee
    username: Column[str] = Column(
        Text,
        ForeignKey('users.username'),
        nullable=False
    )

    #: the name of the attendee (incl. first / lastname )
    name: Column[str] = Column(Text, nullable=False)

    #: birth date of the attendee for the age calculation
    birth_date: Column[date] = Column(Date, nullable=False)

    #: we use text for possible gender fluidity in the future ;)
    gender: Column[str | None] = Column(Text, nullable=True)

    #: notes about the attendee by the parents (e.g. allergies)
    notes: Column[str | None] = Column(Text, nullable=True)

    #: SwissPass ID of the attendee
    swisspass: Column[str | None] = Column(Text, nullable=True)

    #: if the address of the attendee differs from the user address
    differing_address: Column[bool] = Column(
        Boolean,
        default=False,
        nullable=False
    )

    #: address of the attendee (street and number)
    address: Column[str | None] = Column(Text, nullable=True)

    #: zip code of the attendee
    zip_code: Column[str | None] = Column(Text, nullable=True)

    #: place of the attendee
    place: Column[str | None] = Column(Text, nullable=True)

    #: political municipality, only if activated in settings
    political_municipality: Column[str | None] = Column(Text, nullable=True)

    #: the maximum number of bookings the attendee wishes to get in each period
    limit: Column[int | None] = Column(Integer, nullable=True)

    #: access the user linked to this booking
    user: relationship[User] = relationship('User')

    #: a secondary id used for subscriptions only - subscriptions are ical urls
    #: with public permission, by using a separate id we mitigate the risk of
    #: someone figuring out all the attendee ids and gaining access to the
    #: the calendars of all attendees
    #:
    #: furthermore, subscription ids can be changed in the future to invalidate
    #: all existing subscription urls for one or all attendees.
    subscription_token: Column[str] = Column(
        Text,
        nullable=False,
        unique=True,
        default=random_token
    )

    @validates('gender')
    def validate_gender(self, field: str, value: str | None) -> str | None:
        # for now we stay old-fashioned
        assert value in (None, 'male', 'female')
        return value

    if TYPE_CHECKING:
        age: Column[int]
        happiness: _HybridMethod[[uuid.UUID], float | None]

    @hybrid_property  # type:ignore[no-redef]
    def age(self) -> int:
        today = date.today()
        birth = self.birth_date
        extra = (today.month, today.day) < (birth.month, birth.day) and 1 or 0

        return today.year - birth.year - extra

    @age.expression  # type:ignore[no-redef]
    def age(cls) -> ColumnElement[int]:
        return func.extract('year', func.age(cls.birth_date))

    @hybrid_method  # type:ignore[no-redef]
    def happiness(self, period_id: uuid.UUID) -> float | None:
        """ Returns the happiness of the attende in the given period.

        The happiness is a value between 0.0 and 1.0, indicating how many
        of the bookings on the wishlist were fulfilled.

        If all bookings were fulfilled, the happiness is 1.0, if no bookings
        were fulfilled the hapiness is 0.0.

        The priority of the bookings is taken into account. The decision on
        a high-priority booking has a higher impact than the decision on a
        low-priority booking. To model this we simply multiply the booking
        priority when summing up the happiness. So if a booking with priority
        1 is accepted, it is as if 2 bookings were accepted. If a booking
        with priority 1 is denied, it is as if 2 bookings were denied.

        """

        score = 0
        score_max = 0

        bookings = (b for b in self.bookings if b.period_id == period_id)

        for booking in bookings:
            score += booking.state == 'accepted' and booking.priority + 1
            score_max += booking.priority + 1

        # attendees without a booking have no known happiness (incidentally,
        # this works well with the sql expression below -> other default values
        # are harder to come by)
        if not score_max:
            return None

        return score / score_max

    @happiness.expression  # type:ignore[no-redef]
    def happiness(
        cls,
        period_id: uuid.UUID
    ) -> ColumnElement[float | None]:
        return select([
            # force the result to be a float instead of a decimal
            type_coerce(
                func.sum(
                    case([
                        (Booking.state == 'accepted', Booking.priority + 1),
                    ], else_=0)
                ) / cast(
                    # force the division to produce a float instead of an int
                    func.sum(Booking.priority) + func.count(Booking.id), Float
                ),
                Numeric(asdecimal=False)
            )
        ]).where(and_(
            Booking.period_id == period_id,
            Booking.attendee_id == cls.id
        )).label('happiness')

    #: The bookings linked to this attendee
    bookings: relationship[list[Booking]] = relationship(
        'Booking',
        order_by='Booking.created',
        back_populates='attendee'
    )

    __table_args__ = (
        Index('unique_child_name', 'username', 'name', unique=True),
    )
