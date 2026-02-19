from __future__ import annotations

from datetime import date
from onegov.activity.models.booking import Booking
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.crypto import random_token
from onegov.search import ORMSearchable
from sqlalchemy import case, cast, func, select, and_, type_coerce
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Numeric
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import mapped_column, relationship, validates, Mapped
from translationstring import TranslationString
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.user import User
    from sqlalchemy.sql import ColumnElement


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
    fts_title_property = 'title'
    fts_properties = {
        'username': {'type': 'text', 'weight': 'A'},
        'name': {'type': 'text', 'weight': 'A'},
        'notes': {'type': 'localized', 'weight': 'C'}
    }
    fts_public = False

    @property
    def fts_suggestion(self) -> str:
        return self.name

    @property
    def title(self) -> str:
        return f'{self.username} {self.name}'

    def __hash__(self) -> int:
        return hash(self.id)

    #: the public id of the attendee
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the user owning the attendee
    username: Mapped[str] = mapped_column(ForeignKey('users.username'))

    #: the name of the attendee (incl. first / lastname )
    name: Mapped[str]

    #: birth date of the attendee for the age calculation
    birth_date: Mapped[date]

    #: we use text for possible gender fluidity in the future ;)
    gender: Mapped[str | None]

    #: notes about the attendee by the parents (e.g. allergies)
    notes: Mapped[str | None]

    #: SwissPass ID of the attendee
    swisspass: Mapped[str | None]

    #: if the address of the attendee differs from the user address
    differing_address: Mapped[bool] = mapped_column(default=False)

    #: address of the attendee (street and number)
    address: Mapped[str | None]

    #: zip code of the attendee
    zip_code: Mapped[str | None]

    #: place of the attendee
    place: Mapped[str | None]

    #: political municipality, only if activated in settings
    political_municipality: Mapped[str | None]

    #: the maximum number of bookings the attendee wishes to get in each period
    limit: Mapped[int | None]

    #: access the user linked to this booking
    user: Mapped[User] = relationship()

    #: a secondary id used for subscriptions only - subscriptions are ical urls
    #: with public permission, by using a separate id we mitigate the risk of
    #: someone figuring out all the attendee ids and gaining access to the
    #: the calendars of all attendees
    #:
    #: furthermore, subscription ids can be changed in the future to invalidate
    #: all existing subscription urls for one or all attendees.
    subscription_token: Mapped[str] = mapped_column(
        unique=True,
        default=random_token
    )

    @validates('gender')
    def validate_gender(self, field: str, value: str | None) -> str | None:
        # for now we stay old-fashioned
        assert value in (None, 'male', 'female')
        return value

    @hybrid_property
    def age(self) -> int:
        today = date.today()
        birth = self.birth_date
        extra = (today.month, today.day) < (birth.month, birth.day) and 1 or 0

        return today.year - birth.year - extra

    @age.inplace.expression
    @classmethod
    def _age_expression(cls) -> ColumnElement[int]:
        return func.extract('year', func.age(cls.birth_date))

    @hybrid_method
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

    @happiness.expression
    @classmethod
    def _happiness_expression(
        cls,
        period_id: uuid.UUID
    ) -> ColumnElement[float | None]:
        return select(
            # force the result to be a float instead of a decimal
            type_coerce(
                func.sum(
                    case(
                        (Booking.state == 'accepted', Booking.priority + 1),
                        else_=0
                    )
                ) / cast(
                    # force the division to produce a float instead of an int
                    func.sum(Booking.priority) + func.count(Booking.id), Float
                ),
                Numeric(asdecimal=False)
            )
        ).where(and_(
            Booking.period_id == period_id,
            Booking.attendee_id == cls.id
        )).label('happiness')

    #: The bookings linked to this attendee
    bookings: Mapped[list[Booking]] = relationship(
        order_by='Booking.created',
        back_populates='attendee'
    )

    __table_args__ = (
        Index('unique_child_name', 'username', 'name', unique=True),
    )
