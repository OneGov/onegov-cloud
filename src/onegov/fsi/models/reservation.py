from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Boolean, Table
from onegov.core.orm import Base
from onegov.core.orm.types import UUID


reservation_table = Table(
    'fsi_reservations',
    Base.metadata,
    Column('id', UUID, primary_key=True, default=uuid4),
    Column('course_event_id', UUID, ForeignKey('fsi_course_events.id')),
    Column('attendee_id', UUID, ForeignKey('fsi_attendees.id')),
    Column('event_completed', Boolean, default=False, nullable=False)
)


class Reservation(Base):
    __table__ = reservation_table
    __mapper_args__ = {
        'confirm_deleted_rows': False
    }
