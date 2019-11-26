from onegov.fsi.models.course_event import (
    COURSE_EVENT_STATUSES_TRANSLATIONS, COURSE_EVENT_STATUSES
)
from onegov.fsi.models.course_notification_template import \
    NOTIFICATION_TYPE_TRANSLATIONS, NOTIFICATION_TYPES
from onegov.org.layout import DefaultLayout as BaseLayout


class DefaultLayout(BaseLayout):

    def include_accordion(self):
        self.request.include('accordion')

    def instance_link(self, instance):
        return self.request.link(instance)

    @staticmethod
    def format_status(model_status):
        return COURSE_EVENT_STATUSES_TRANSLATIONS[
            COURSE_EVENT_STATUSES.index(model_status)
        ]

    @staticmethod
    def format_notification_type(notification_type):
        return NOTIFICATION_TYPE_TRANSLATIONS[
            NOTIFICATION_TYPES.index(notification_type)
        ]

