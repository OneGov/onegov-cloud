from cached_property import cached_property

from onegov.core.elements import Link, LinkGroup
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.models.course_event import COURSE_EVENT_STATUSES_TRANSLATIONS, \
    COURSE_EVENT_STATUSES
from onegov.org.layout import DefaultLayout as OrgDefaultLayout
from onegov.org.layout import DefaultMailLayout as OrgDefaultMailLayout
from onegov.org.layout import Layout as OrgBaseLayout
from onegov.fsi import _


class Layout(OrgBaseLayout):
    pass


class DefaultLayout(OrgDefaultLayout):
    pass


# class CourseLayout(DefaultLayout):
#
#     @cached_property
#     def editbar_links(self):
#         links = []
#         if self.request.is_admin:
#             links.append(
#                 Link(
#                     text=_("Add Course"),
#                     url=self.request.class_link(
#                         CourseEventCollection, name='new'
#                     ),
#                     attrs={'class': 'new-item'}
#                 )
#             )
#
#         return links


class CourseEventLayout(DefaultLayout):

    def upcoming_events(self, limit):
        raise NotImplementedError
        # return self.request.link(CourseEventCollection(
        #     self.session,
        #     upcoming_only=True,
        #     limit=limit
        # ))

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        links = [Link(_("Homepage"), self.homepage_url)]
        if self.request.is_admin:
            links.append(
                Link(_('Course management',
                       self.request.class_link(CourseEventCollection))))
        else:
            links.append(
                Link(_('Courses',
                       self.request.class_link(CourseEventCollection))))
        return links

    @cached_property
    def editbar_links(self):
        links = []
        if self.request.is_manager:
            links.append(
                Link(
                    text=_("Add Course Event"),
                    url=self.request.class_link(
                        CourseEventCollection, name='new'
                    ),
                    attrs={'class': 'new-item'}
                )
            )
        return links

    @cached_property
    def title(self):

        if self.model.limit is not None:
            return _('Upcoming Course Events')

        if self.request.view_name == '':
            return _('Course Events')

        return 'Default Title'

    def format_status(self, model_status):
        return COURSE_EVENT_STATUSES_TRANSLATIONS[
            COURSE_EVENT_STATUSES.index(model_status)
        ]

    def instance_link(self, instance):
        return self.request.link(instance)


class ReservationLayout(DefaultLayout):
    pass


class MailLayout(OrgDefaultMailLayout):

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
