from onegov.fsi.models.course_attendee import ATTENDEE_TITLE_TRANSLATIONS, \
    ATTENDEE_TITLES
from onegov.fsi.models.course_event import (
    COURSE_EVENT_STATUSES_TRANSLATIONS, COURSE_EVENT_STATUSES
)
from onegov.fsi.models.notification_template import \
    NOTIFICATION_TYPE_TRANSLATIONS, NOTIFICATION_TYPES
from onegov.org.layout import DefaultLayout as OrgDefaultLayout
from onegov.org.layout import Layout as OrgBaseLayout


class Layout(OrgBaseLayout):
    pass


class DefaultLayout(OrgDefaultLayout):

    def include_accordion(self):
        self.request.include('accordion')

    def include_editor(self):
        self.request.include('redactor')
        self.request.include('editor')

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

    @staticmethod
    def format_salutation(title):
        return ATTENDEE_TITLE_TRANSLATIONS[
            ATTENDEE_TITLES.index(title)
        ]
