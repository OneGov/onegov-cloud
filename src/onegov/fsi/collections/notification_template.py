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


class CourseNotificationTemplateCollection(GenericCollection):

    def __init__(self, session, course_event_id=None):
        super().__init__(session)
        self.course_event_id = course_event_id

    @cached_property
    def model_class(self):
        return CourseNotificationTemplate

    @cached_property
    def course_event(self):
        return self.session.query(CourseEvent).filter_by(
            id=self.course_event_id).first()

    def query(self):
        query = super().query()
        if self.course_event_id:
            query = query.filter_by(course_event_id=self.course_event_id)
        return query

    @cached_property
    def course_reservations(self):
        return self.course_event.subscriptions

    def auto_add_templates_if_not_existing(self):
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
