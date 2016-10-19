from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import column
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Index
from sqlalchemy import Text
from sqlalchemy.orm import object_session, relationship
from uuid import uuid4


class Period(Base, TimestampMixin):

    __tablename__ = 'periods'

    #: The public id of this period
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The public title of this period
    title = Column(Text, nullable=False)

    #: Only one period is active at a time
    active = Column(Boolean, nullable=False, default=False)

    #: Start of the wishlist-phase
    prebooking_start = Column(Date, nullable=False)

    #: End of the wishlist-phase
    prebooking_end = Column(Date, nullable=False)

    #: Date of the earliest possible occasion start of this period
    execution_start = Column(Date, nullable=False)

    #: Date of the latest possible occasion end of this period
    execution_end = Column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint((
            '"prebooking_start" <= "prebooking_end" AND '
            '"prebooking_end" <= "execution_start" AND '
            '"execution_start" <= "execution_end"'
        ), name='period_date_order'),
        Index(
            'only_one_active_period', 'active',
            unique=True, postgresql_where=column('active') == True
        )
    )

    #: The occasions linked to this period
    occasions = relationship(
        'Occasion',
        order_by='Occasion.start',
        backref='period'
    )

    #: The bookings linked to this period
    bookings = relationship(
        'Booking',
        backref='period'
    )

    def activate(self):
        """ Activates the current period, causing all occasions and activites
        to update their status and book-keeping.

        It also makes sure no other period is active.

        """
        if self.active:
            return

        session = object_session(self)
        model = self.__class__

        active_period = session.query(model)\
            .filter(model.active == True).first()

        if active_period:
            active_period.deactivate()

        # avoid triggering the only_one_active_period index constraint
        session.flush()

        self.active = True

    def deactivate(self):
        """ Deactivates the current period, causing all occasions and activites
        to update their status and book-keeping.

        """

        if not self.active:
            return

        self.active = False
