from __future__ import annotations

from functools import cached_property

from onegov.core.elements import Link, LinkGroup
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.notification_template import (
    CourseNotificationTemplateCollection)
from onegov.fsi.layout import DefaultLayout, FormatMixin
from onegov.org.layout import DefaultMailLayout as OrgDefaultMailLayout
from onegov.fsi import _


from typing import NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from chameleon import PageTemplateFile
    from onegov.core.templates import MacrosLookup
    from onegov.fsi.app import FsiApp
    from onegov.fsi.models import CourseEvent, CourseNotificationTemplate
    from onegov.fsi.request import FsiRequest


class MailLayout(OrgDefaultMailLayout, FormatMixin):

    """Layout for emails expecting the model to be a subscription object.
    Takes in a notification template linked to a course_event.
    """

    app: FsiApp
    request: FsiRequest
    model: CourseNotificationTemplate

    @property
    def title(self) -> str:
        return _(
            'Preview Info Mail for ${course_event}',
            mapping={'course_event': self.model.course_event.name}
        )

    @cached_property
    def default_macros(self) -> MacrosLookup:
        return self.template_loader.macros

    @cached_property
    def edit_link(self) -> str:
        return self.request.link(self.model, name='edit')

    @cached_property
    def base(self) -> PageTemplateFile:
        return self.template_loader['mail_layout.pt']

    @cached_property
    def event_start(self) -> str:
        return self.format_date(
            self.model.course_event.start, 'time')

    @cached_property
    def event_end(self) -> str:
        return self.format_date(self.model.course_event.end, 'time')

    @cached_property
    def event_date(self) -> str:
        return self.format_date(self.model.course_event.end, 'date')

    @cached_property
    def course_name(self) -> str:
        return self.model.course_event.course.name

    @cached_property
    def course_description(self) -> str:
        return self.model.course_event.course.description

    @cached_property
    def reservation_name(self) -> str:
        return str(self.model)

    @cached_property
    def event_url(self) -> str:
        return self.request.link(self.model.course_event)

    @cached_property
    def course_url(self) -> str:
        return self.request.link(self.model.course_event.course)

    @cached_property
    def upcoming_events_collection(self) -> CourseEventCollection:
        return CourseEventCollection(
            self.request.session,
            course_id=self.model.course_event.course.id,
            upcoming_only=True)

    @cached_property
    def open_events_url(self) -> str:
        return self.request.link(self.upcoming_events_collection)

    @cached_property
    def events_list(self) -> list[CourseEvent]:
        return self.upcoming_events_collection.query().all()

    @cached_property
    def notification_type(self) -> str:
        return self.model.type


class NotificationTemplateCollectionLayout(DefaultLayout):

    model: CourseNotificationTemplateCollection

    @property
    def title(self) -> str:
        return _('Manage Notification Templates')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        assert self.model.course_event is not None
        links.append(
            Link(self.model.course_event.name, self.request.link(
                self.model.course_event))
        )
        links.append(
            Link(_('Manage Notification Templates'),
                 self.request.link(self.model)),
        )
        return links

    class AccordionItem(NamedTuple):
        subject: str | None
        text: str | None
        url: str
        edit_url: str

    def accordion_items(self) -> tuple[AccordionItem, ...]:
        return tuple(
            self.AccordionItem(
                item.subject,
                item.text,
                self.request.link(item),
                self.request.link(item, name='edit')
            ) for item in self.model.query()
        )


class NotificationTemplateLayout(DefaultLayout):

    model: CourseNotificationTemplate

    @cached_property
    def title(self) -> str:
        return _(
            'Notification Template ${type}',
            mapping={'type': self.request.translate(
                self.format_notification_type(self.model.type))}
        )

    @cached_property
    def collection(self) -> CourseNotificationTemplateCollection:
        return CourseNotificationTemplateCollection(
            self.request.session,
            course_event_id=self.model.course_event_id
        )

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(Link(self.model.course_event.name,
                          self.request.link(self.model.course_event)))
        links.append(Link(_('Manage Notification Templates'),
                          self.request.link(self.collection)))
        links.append(Link(self.format_notification_type(self.model.type),
                          self.request.link(self.model)))
        return links

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []
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
    def title(self) -> str:
        return _(
            'Edit ${type}',
            mapping={'type': self.request.translate(
                self.format_notification_type(self.model.type))}
        )

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        links.append(
            Link(_('Edit'), self.request.link(self.model, name='edit')))
        return links


class SendNotificationTemplateLayout(NotificationTemplateLayout):
    @property
    def title(self) -> str:
        return _('Mailing')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        breadcrumbs = super().breadcrumbs
        breadcrumbs.append(Link(_('Send')))
        return breadcrumbs
