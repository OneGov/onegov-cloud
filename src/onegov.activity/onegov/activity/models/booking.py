from onegov.activity.models.occasion import Occasion
from onegov.activity.utils import random_group_code
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Enum, Text, ForeignKey, Integer
from uuid import uuid4


class Booking(Base, TimestampMixin):
    """ Bookings are created by users for occasions.

    Initially, bookings are unconfirmed. In this state they represent
    a "wish" rather than a probably booking.

    Because bookings are wishes initially, they get a priority as well as
    a group code which links multiple bookings by multiple users together.

    They system will try to figure out the best booking using the priority
    as well as the group code.

    """

    __tablename__ = 'bookings'

    #: the public id of the booking
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the user owning the booking
    username = Column(Text, ForeignKey('users.username'), nullable=False)

    #: the priority of the booking, a higher number = a higher priority
    priority = Column(Integer, nullable=False, default=0)

    #: the group code of the booking
    group_code = Column(Text, nullable=False, default=random_group_code)

    #: the last name of the participant
    last_name = Column(Text, nullable=False)

    #: the first name of the participant
    first_name = Column(Text, nullable=False)

    #: the occasion this booking belongs to
    occasion_id = Column(UUID, ForeignKey(Occasion.id), nullable=False)

    #: the state of the booking
    state = Column(
        Enum('unconfirmed', 'confirmed', 'cancelled', name='booking_state'),
        nullable=False,
        default='unconfirmed'
    )

    __mapper_args__ = {
        'order_by': priority
    }

    def confirm(self):
        assert self.state == 'unconfirmed'
        self.state = 'confirmed'

    def cancel(self):
        assert self.state in ('confirmed', 'unconfirmed')
        self.state = 'cancel'
