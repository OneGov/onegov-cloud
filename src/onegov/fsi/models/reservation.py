from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Boolean, Table, Text
from onegov.core.orm import Base
from onegov.core.orm.types import UUID, UTCDateTime

table_name = 'fsi_reservations'

reservation_table = Table(
    table_name,
    Base.metadata,
    Column('id', UUID, primary_key=True, default=uuid4),
    Column('course_event_id', UUID,
           ForeignKey('fsi_course_events.id'), nullable=False),
    Column('attendee_id', UUID, ForeignKey('fsi_attendees.id')),
    Column('event_completed', Boolean, default=False, nullable=False),
    Column('dummy_desc', Text),

    # Fields for the NotificationTemplate.NOTIFICATION_TYPES
    Column('invitation_sent', UTCDateTime),
    Column('reminder_sent', UTCDateTime),
    Column('cancellation_sent', UTCDateTime),
    Column('info_sent', UTCDateTime)
)


class Reservation(Base):
    """Linking table between CourseEvent and CourseAttendee.
    This table is defined in a way such that i can be used for a secondary
    join in CourseEvent.attendees.

    attendee_id is Null if its a placeholder reservation.

    """
    __table__ = reservation_table
    __tablename__ = table_name
    __mapper_args__ = {
        'confirm_deleted_rows': False
    }

    @property
    def is_placeholder(self):
        return self.attendee_id is None

    @classmethod
    def as_placeholder(cls, dummy_desc, **kwargs):
        assert 'attendee_id' not in kwargs
        return cls(dummy_desc=dummy_desc, **kwargs)

    def __str__(self):
        if self.is_placeholder:
            return f'{self.dummy_desc or ""}'
        return f'{self.attendee.last_name}, {self.attendee.first_name}'
