from __future__ import annotations

from onegov.core.orm import Base
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import Boolean, Text, UUID as UUIDType
from sqlalchemy.orm import relationship, Mapped
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.request import FsiRequest
    from .course_attendee import CourseAttendee
    from .course_event import CourseEvent


table_name = 'fsi_reservations'
subscription_table = Table(
    table_name,
    Base.metadata,
    Column('id', UUIDType(as_uuid=True), primary_key=True, default=uuid4),
    Column('course_event_id', UUIDType(as_uuid=True),
           ForeignKey('fsi_course_events.id'), nullable=False),
    Column('attendee_id', UUIDType(as_uuid=True),
           ForeignKey('fsi_attendees.id')),
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
        id: Mapped[UUID]
        course_event_id: Mapped[UUID]
        attendee_id: Mapped[UUID | None]
        event_completed: Mapped[bool]
        dummy_desc: Mapped[str | None]

    course_event: Mapped[CourseEvent] = relationship(
        back_populates='subscriptions',
        lazy='joined'
    )
    attendee: Mapped[CourseAttendee | None] = relationship(
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
