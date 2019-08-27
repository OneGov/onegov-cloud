from datetime import date
from onegov.activity.models.booking import Booking
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.crypto import random_token
from onegov.search import ORMSearchable
from sqlalchemy import case, cast, func, select, and_, type_coerce
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
from uuid import uuid4


class Attendee(Base, TimestampMixin, ORMSearchable):
    """ Attendees are linked to zero to many bookings. Each booking
    has an attendee.

    Though an attendee may be the same person as a username in reality, in the
    model we treat those subjects as separate.

    """

    __tablename__ = 'attendees'

    es_properties = {
        'username': {'type': 'text'},
        'name': {'type': 'text'},
        'notes': {'type': 'localized'}
    }
    es_public = False

    @property
    def es_suggestion(self):
        return self.name

    def __hash__(self):
        return hash(self.id)

    #: the public id of the attendee
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the user owning the attendee
    username = Column(Text, ForeignKey('users.username'), nullable=False)

    #: the name of the attendee (incl. first / lastname )
    name = Column(Text, nullable=False)

    #: birth date of the attendee for the age calculation
    birth_date = Column(Date, nullable=False)

    #: we use text for possible gender fluidity in the future ;)
    gender = Column(Text, nullable=True)

    #: notes about the attendee by the parents (e.g. allergies)
    notes = Column(Text, nullable=True)

    #: the maximum number of bookings the attendee wishes to get in each period
    limit = Column(Integer, nullable=True)

    #: access the user linked to this booking
    user = relationship('User')

    #: a secondary id used for subscriptions only - subscriptions are ical urls
    #: with public permission, by using a separate id we mitigate the risk of
    #: someone figuring out all the attendee ids and gaining access to the
    #: the calendars of all attendees
    #:
    #: furthermore, subscription ids can be changed in the future to invalidate
    #: all existing subscription urls for one or all attendees.
    subscription_token = Column(
        Text, nullable=False, unique=True, default=random_token)

    @validates('gender')
    def validate_gender(self, field, value):
        # for now we stay old-fashioned
        assert value in (None, 'male', 'female')
        return value

    @hybrid_property
    def age(self):
        today = date.today()
        birth = self.birth_date
        extra = (today.month, today.day) < (birth.month, birth.day) and 1 or 0

        return today.year - birth.year - extra

    @age.expression
    def age(self):
        return func.extract('year', func.age(self.birth_date))

    @hybrid_method
    def happiness(self, period_id):
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
    def happiness(cls, period_id):
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
        )).label("happiness")

    #: The bookings linked to this attendee
    bookings = relationship(
        'Booking',
        order_by='Booking.created',
        backref='attendee'
    )

    __table_args__ = (
        Index('unique_child_name', 'username', 'name', unique=True),
    )
