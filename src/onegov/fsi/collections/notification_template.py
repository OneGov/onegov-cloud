from cached_property import cached_property

from onegov.core.collection import GenericCollection
from onegov.fsi.models.notification_template import FsiNotificationTemplate, \
    InfoTemplate, ReservationTemplate, CancellationTemplate, ReminderTemplate


class FsiNotificationTemplateCollection(GenericCollection):

    def __init__(self, session, course_event_id=None):
        super().__init__(session)
        self.course_event_id = course_event_id

    @cached_property
    def model_class(self):
        return FsiNotificationTemplate

    @cached_property
    def course_event(self):
        return self.by_id(self.course_event_id) if self.course_event else None

    def query(self):
        query = super().query()
        if self.course_event_id:
            query = query.filter_by(course_event_id=self.course_event_id)
        return query

    @cached_property
    def course_reservations(self):
        return self.course_event.reservations

    def auto_add_templates_if_not_existing(self):
        assert self.course_event_id
        if self.query().count() == 0:
            # Owner id should be set in path.py if not present
            data = dict(course_event_id=self.course_event_id)
            self.session.add_all((
                InfoTemplate(**data),
                ReservationTemplate(**data),
                CancellationTemplate(**data),
                ReminderTemplate(**data)
            ))
            self.session.flush()
