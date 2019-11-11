from collections import namedtuple

from cached_property import cached_property

from onegov.core.elements import Link
from onegov.fsi.layout import DefaultLayout
from onegov.org.layout import DefaultMailLayout as OrgDefaultMailLayout
from onegov.fsi import _


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

    @cached_property
    def course_event_url(self):
        return self.request.link(self.model.course_event)


class NotificationTemplateLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _('Notification Template Details')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(_('Current Notification Template'),
                          self.request.link(self.model)))
        return links

    @cached_property
    def editbar_links(self):
        return [
            Link(_('Edit'), self.request.link(self.model, name='edit'),
                 attrs={'class': 'edit-icon'})
        ]


class EditNotificationTemplateLayout(NotificationTemplateLayout):
    @cached_property
    def title(self):
        return _('Edit Notification Template')

    @cached_property
    def editbar_links(self):
        links = super().editbar_links
        links.append(Link(_('Edit'), '#'))
        return links


class NotificationTemplateCollectionLayout(DefaultLayout):
    @cached_property
    def title(self):
        return _('Manage Notification Templates')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(_('Manage Notification Templates')))
        return links

    def accordion_items(self):
        template = namedtuple('Template',
                              ['subject', 'text', 'url', 'edit_url'])
        return tuple(
            template(
                item.subject,
                item.text,
                self.request.link(item),
                self.request.link(item, name='edit')
            ) for item in self.model.query()
        )
