from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Boolean, Table, MetaData
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
    # __tablename__ = 'fsi_reservations'
    __table__ = reservation_table

    # id = Column(UUID, primary_key=True, default=uuid4)
    #
    # course_event_id = Column(
    #     UUID, ForeignKey('fsi_course_events.id'), nullable=False)
    # attendee_id = Column(
    #     UUID, ForeignKey('fsi_attendees.id'), nullable=False)
    #
    # event_completed = Column(Boolean, default=False, nullable=False)
