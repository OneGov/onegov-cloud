from sqlalchemy import event

from onegov.fsi.models.course_attendee import ATTENDEE_TITLE_TRANSLATIONS, \
    ATTENDEE_TITLES
from onegov.fsi.models.course_event import (
    COURSE_EVENT_STATUSES_TRANSLATIONS, COURSE_EVENT_STATUSES
)
from onegov.fsi.models.notification_template import \
    NOTIFICATION_TYPE_TRANSLATIONS, NOTIFICATION_TYPES
from onegov.org.layout import DefaultLayout as OrgDefaultLayout
from onegov.org.layout import Layout as OrgBaseLayout


class SessionEventMixin(object):

    @property
    def target_model(self):
        if hasattr(self.model, 'model_class'):
            return self.model.model_class
        if hasattr(self.__class__, 'primary_key'):
            return self.__class__
        raise NotImplementedError

    def session_event_callback(self, session, instance):
        raise NotImplementedError

    def register_event(self):

        @event.listens_for(self.session, 'loaded_as_persistent')
        def receive_loaded_as_persistent(session, instance):
            "listen for the 'loaded_as_persistent' event"

            if isinstance(instance, self.target_model):
                self.session_event_callback(session, instance)


class Layout(OrgBaseLayout):
    pass


class DefaultLayout(OrgDefaultLayout):

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
