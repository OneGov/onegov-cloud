from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from sqlalchemy import Column, ForeignKey, Boolean, Table, Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.fsi.request import FsiRequest
    from .course_attendee import CourseAttendee
    from .course_event import CourseEvent


table_name = 'fsi_reservations'
subscription_table = Table(
    table_name,
    Base.metadata,
    Column('id', UUID, primary_key=True, default=uuid4),
    Column('course_event_id', UUID,
           ForeignKey('fsi_course_events.id'), nullable=False),
    Column('attendee_id', UUID, ForeignKey('fsi_attendees.id')),
    # If the attendee completed the event
    Column('event_completed', Boolean, default=False, nullable=False),
    Column('dummy_desc', Text),

)


class CourseSubscription(Base):
    """Linking table between CourseEvent and CourseAttendee.
    This table is defined in a way such that it can be used for a secondary
    join in CourseEvent.attendees.

    attendee_id is Null if its a placeholder subscription.

    """
    __table__ = subscription_table
    __tablename__ = table_name
    __mapper_args__ = {
        'confirm_deleted_rows': False
    }

    if TYPE_CHECKING:
        # NOTE: We need to forward declare the table columns the mapper will
        #       add on our behalf based on __table__, this is a bit fragile
        #       can we not just use CourseSubscription.__table__ for the
        #       secondary join and use a regular model?
        id: Column[uuid.UUID]
        course_event_id: Column[uuid.UUID]
        attendee_id: Column[uuid.UUID | None]
        event_completed: Column[bool]
        dummy_desc: Column[str | None]

    course_event: relationship[CourseEvent] = relationship(
        'CourseEvent',
        back_populates='subscriptions',
        lazy='joined'
    )
    attendee: relationship[CourseAttendee | None] = relationship(
        'CourseAttendee',
        back_populates='subscriptions',
    )

    @property
    def is_placeholder(self) -> bool:
        return self.attendee_id is None

    def can_be_confirmed(self, request: FsiRequest) -> bool:
        if not request.is_admin:
            return False
        event = self.course_event
        return event.is_past and event.status == 'confirmed'

    def __str__(self) -> str:
        if self.is_placeholder:
            return f'{self.dummy_desc or ""}'
        return str(self.attendee)
