from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Boolean
from onegov.core.orm import Base
from onegov.core.orm.types import UUID


class Reservation(Base):

    __tablename__ = 'fsi_reservations'

    id = Column(UUID, primary_key=True, default=uuid4)
    course_id = Column(UUID, ForeignKey('fsi_courses.id'), nullable=False)
    attendee_id = Column(UUID, ForeignKey('fsi_attendees.id'), nullable=False)
    event_completed = Column(Boolean, default=False, nullable=False)
