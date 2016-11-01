from datetime import date, timedelta
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Date, Index, Text, ForeignKey, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from uuid import uuid4


class Attendee(Base, TimestampMixin):
    """ Attendees are linked to zero to many bookings. Each booking
    has an attendee.

    Though an attendee may be the same person as a username in reality, in the
    model we treat those subjects as separate.

    """

    __tablename__ = 'attendees'

    #: the public id of the attendee
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the user owning the attendee
    username = Column(Text, ForeignKey('users.username'), nullable=False)

    #: the name of the attendee (incl. first / lastname )
    name = Column(Text, nullable=False)

    #: birth date of the attendee for the age calculation
    birth_date = Column(Date, nullable=False)

    def __hash__(self):
        return hash(self.id)

    @hybrid_property
    def age(self):
        return (date.today() - self.birth_date) // timedelta(days=365.2425)

    @age.expression
    def age(self):
        return func.extract('year', func.age(self.birth_date))

    #: The bookings linked to this attendee
    bookings = relationship(
        'Booking',
        order_by='Booking.created',
        backref='attendee'
    )

    __table_args__ = (
        Index('unique_child_name', 'username', 'name', unique=True),
    )
