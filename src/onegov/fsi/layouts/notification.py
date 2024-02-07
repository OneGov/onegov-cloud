from collections import namedtuple

from functools import cached_property

from onegov.core.elements import Link
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.notification_template import (
    CourseNotificationTemplateCollection)
from onegov.fsi.layout import DefaultLayout, FormatMixin
from onegov.org.layout import DefaultMailLayout as OrgDefaultMailLayout
from onegov.fsi import _


class MailLayout(OrgDefaultMailLayout, FormatMixin):  # type:ignore[misc]

    """Layout for emails expecting the model to be a subscription object.
    Takes in a notification template linked to a course_event.
    """

    @cached_property
    def title(self):
        return _(
            'Preview Info Mail for ${course_event}',
            mapping={'course_event': self.model.course_event.name}
        )

    @cached_property
    def default_macros(self):
        return self.template_loader.macros

    @cached_property
    def edit_link(self):
        return self.request.link(self.model, name='edit')

    @cached_property
    def base(self):
        return self.template_loader['mail_layout.pt']

    @cached_property
    def event_start(self):
        return self.format_date(
            self.model.course_event.start, 'time')

    @cached_property
    def event_end(self):
        return self.format_date(self.model.course_event.end, 'time')

    @cached_property
    def event_date(self):
        return self.format_date(self.model.course_event.end, 'date')

    @cached_property
    def course_name(self):
        return self.model.course_event.course.name

    @cached_property
    def course_description(self):
        return self.model.course_event.course.description

    @cached_property
    def reservation_name(self):
        return str(self.model)

    @cached_property
    def event_url(self):
        return self.request.link(self.model.course_event)

    @cached_property
    def course_url(self):
        return self.request.link(self.model.course_event.course)

    @cached_property
    def upcoming_events_collection(self):
        return CourseEventCollection(
            self.request.session,
            course_id=self.model.course_event.course.id,
            upcoming_only=True)

    @cached_property
    def open_events_url(self):
        return self.request.link(self.upcoming_events_collection)

    @cached_property
    def events_list(self):
        return self.upcoming_events_collection.query().all()

    @cached_property
    def notification_type(self):
        return self.model.type


class NotificationTemplateCollectionLayout(DefaultLayout):
    @cached_property
    def title(self):
        return _('Manage Notification Templates')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(
            Link(self.model.course_event.name, self.request.link(
                self.model.course_event))
        )
        links.append(
            Link(_('Manage Notification Templates'),
                 self.request.link(self.model)),
        )
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


class NotificationTemplateLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _(
            'Notification Template ${type}',
            mapping={'type': self.request.translate(
                self.format_notification_type(self.model.type))}
        )

    @cached_property
    def collection(self):
        return CourseNotificationTemplateCollection(
            self.request.session,
            course_event_id=self.model.course_event_id
        )

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(self.model.course_event.name,
                          self.request.link(self.model.course_event)))
        links.append(Link(_('Manage Notification Templates'),
                          self.request.link(self.collection)))
        links.append(Link(self.format_notification_type(self.model.type),
                          self.request.link(self.model)))
        return links

    @cached_property
    def editbar_links(self):
        links = []
        view_name = self.request.view_name

        if view_name != 'edit':
            links.append(
                Link(
                    _('Add or edit additional Information'),
                    self.request.link(self.model, name='edit'),
                    attrs={'class': 'edit-link'}
                )
            )
        if view_name != 'send' and self.model.type == 'info':
            links.append(
                Link(
                    _('Send'),
                    self.request.link(self.model, name='send'),
                    attrs={'class': 'email-link'},
                )
            )

        return links


class EditNotificationTemplateLayout(NotificationTemplateLayout):
    @cached_property
    def title(self):
        return _(
            'Edit ${type}',
            mapping={'type': self.request.translate(
                self.format_notification_type(self.model.type))}
        )

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(
            Link(_('Edit'), self.request.link(self.model, name='edit')))
        return links


class SendNotificationTemplateLayout(NotificationTemplateLayout):
    @cached_property
    def title(self):
        return _('Mailing')

    @cached_property
    def breadcrumbs(self):
        breadcrumbs = super().breadcrumbs
        breadcrumbs.append(Link(_('Send')))
        return breadcrumbs
