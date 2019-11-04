from cached_property import cached_property

from onegov.core.layout import ChameleonLayout
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.org.layout import DefaultLayout as OrgDefaultLayout


class DefaultLayout(OrgDefaultLayout):

    def events_link(self, course):
        return self.request.link(CourseEventCollection(
            self.session,
            upcoming_only=True,
            course_id=course.id)
        )


class MailLayout(ChameleonLayout):

    """Layout for emails expecting the model to be a reservation object."""

    def __init__(self, *args, notification_type=None):
        super().__init__(*args)
        self.notification_type = notification_type

    @cached_property
    def base(self):
        return self.template_loader['mail_layout.pt']

    @cached_property
    def course_start(self):
        return self.format_date(
            self.model.course_event.start, self.time_format)

    @cached_property
    def course_end(self):
        return self.format_date(self.model.course_event.end, self.time_format)

    @cached_property
    def course_date(self):
        return self.format_date(self.model.course_event.end, self.date_format)

    @cached_property
    def course_name(self):
        return self.model.course.name

    @cached_property
    def course_description(self):
        return self.model.course.description

    @cached_property
    def reservation_name(self):
        return str(self.model)
