from __future__ import annotations

from functools import cached_property

from onegov.core.collection import GenericCollection
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_notification_template import (
    CourseNotificationTemplate,
    InfoTemplate,
    SubscriptionTemplate,
    CancellationTemplate,
    ReminderTemplate,
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.models import CourseSubscription
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


class CourseNotificationTemplateCollection(
    GenericCollection[CourseNotificationTemplate]
):

    def __init__(
        self,
        session: Session,
        course_event_id: UUID | None = None
    ) -> None:
        super().__init__(session)
        self.course_event_id = course_event_id

    @property
    def model_class(self) -> type[CourseNotificationTemplate]:
        return CourseNotificationTemplate

    @cached_property
    def course_event(self) -> CourseEvent | None:
        return self.session.query(CourseEvent).filter_by(
            id=self.course_event_id).first()

    def query(self) -> Query[CourseNotificationTemplate]:
        query = super().query()
        if self.course_event_id:
            query = query.filter_by(course_event_id=self.course_event_id)
        return query

    @cached_property
    def course_reservations(self) -> Query[CourseSubscription]:
        assert self.course_event is not None
        return self.course_event.subscriptions

    def auto_add_templates_if_not_existing(self) -> None:
        assert self.course_event_id
        if not self.query().first():
            # Owner id should be set in path.py if not present
            data = {'course_event_id': self.course_event_id}
            self.session.add_all((
                InfoTemplate(**data),
                SubscriptionTemplate(**data),
                CancellationTemplate(**data),
                ReminderTemplate(**data)
            ))
            self.session.flush()
