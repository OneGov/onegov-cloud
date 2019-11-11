from cached_property import cached_property

from onegov.core.collection import GenericCollection
from onegov.fsi.models.notification_template import FsiNotificationTemplate


class FsiNotificationTemplateCollection(GenericCollection):

    def __init__(self, session, owner_id=None, course_event_id=None):
        super().__init__(session)
        self.owner_id = owner_id
        self.course_event_id = course_event_id

    @cached_property
    def model_class(self):
        return FsiNotificationTemplate

    def query(self):
        query = super().query()
        if self.owner_id:
            query = query.filter_by(owner_id=self.owner_id)
        if self.course_event_id:
            query = query.filter_by(course_event_id=self.course_event_id)
        return query
