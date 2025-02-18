from __future__ import annotations

from functools import cached_property

from onegov.core.elements import Link, Confirm, Intercooler, LinkGroup
from onegov.fsi.collections.audit import AuditCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.notification_template import (
    CourseNotificationTemplateCollection)
from onegov.fsi.collections.subscription import SubscriptionsCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.models import Course, CourseEvent


class CourseEventCollectionLayout(DefaultLayout):

    model: CourseEventCollection

    @cached_property
    def course(self) -> Course | None:
        if self.model.course_id is None:
            return None

        return CourseCollection(self.request.session).by_id(
            self.model.course_id)

    @cached_property
    def title(self) -> str:
        if self.model.past_only:
            return _('Past Course Events')
        return _('Course Events')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        """ Returns the breadcrumbs for the current page. """
        links = super().breadcrumbs
        assert isinstance(links, list)
        if self.course:
            links.append(
                Link(
                    self.course.name,
                    self.request.link(self.course)
                )
            )
        links.append(
            Link(
                _('Course Events'),
                self.request.class_link(CourseEventCollection)))
        return links

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []
        if self.request.is_admin:
            links.append(
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Course Event'),
                            url=self.request.class_link(
                                CourseEventCollection, name='add'
                            ),
                            attrs={'class': 'add-icon'}
                        )
                    ]
                )
            )

        return links

    def subscriptions_link(self, event: CourseEvent) -> str:
        return self.request.link(SubscriptionsCollection(
            self.request.session, course_event_id=event.id))

    def audit_link(self, course: Course | None) -> str | None:
        if not course:
            return None
        assert self.request.attendee is not None
        return self.request.link(AuditCollection(
            self.request.session,
            auth_attendee=self.request.attendee,
            course_id=course.id,
        ))


class CourseEventLayout(DefaultLayout):

    model: CourseEvent

    @property
    def title(self) -> str:
        return _('Course Event Details')

    @cached_property
    def collection(self) -> CourseEventCollection:
        return CourseEventCollection(
            self.request.session,
            show_hidden=True
        )

    @cached_property
    def course_collection(self) -> CourseEventCollection:
        return CourseEventCollection(
            self.request.session,
            show_hidden=True,
            course_id=self.model.course.id
        )

    @cached_property
    def reservation_collection(self) -> SubscriptionsCollection:
        return SubscriptionsCollection(
            self.request.session,
            course_event_id=self.model.id,
            auth_attendee=self.request.attendee
        )

    @cached_property
    def template_collection(self) -> CourseNotificationTemplateCollection:
        return CourseNotificationTemplateCollection(
            self.request.session,
            course_event_id=self.model.id
        )

    @cached_property
    def collection_url(self) -> str:
        return self.request.class_link(CourseEventCollection)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        """ Returns the breadcrumbs for the detail page. """
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(
                self.model.course.name,
                self.request.link(self.model.course)
            )
        )
        links.append(
            Link(
                self.format_date(self.model.start, 'date_long'),
                self.request.link(self.model))
        )
        return links

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:

        add_group_links = [
            Link(
                _('Attendee'),
                self.request.link(
                    SubscriptionsCollection(
                        self.request.session,
                        auth_attendee=self.request.attendee,
                        course_event_id=self.model.id),
                    name='add'
                ),
                attrs={'class': 'add-icon'}
            )
        ]

        if self.request.is_member:
            return []

        if self.request.is_editor and self.model.locked:
            return []

        attendee_link = Link(
            _('Attendees'),
            self.request.link(self.reservation_collection),
            attrs={'class': 'subscriptions'}
        )
        if self.request.is_editor:
            return [
                attendee_link,
                LinkGroup(title=_('Add'), links=add_group_links)
            ]

        add_group_links.extend([
            Link(
                _('External Attendee'),
                self.request.link(
                    SubscriptionsCollection(
                        self.request.session,
                        auth_attendee=self.request.attendee,
                        course_event_id=self.model.id,
                        external_only=True),
                    name='add'
                ),
                attrs={'class': 'add-external'}
            ),
            Link(
                _('Placeholder'),
                self.request.link(
                    self.reservation_collection,
                    name='add-placeholder'
                ),
                attrs={'class': 'add-placeholder'}
            )
        ])

        return [
            LinkGroup(
                title=_('Add'),
                links=add_group_links
            ),
            attendee_link,
            Link(
                _('Edit'),
                self.request.link(self.model, name='edit'),
                attrs={'class': 'edit-link'}
            ),
            Link(
                _('Duplicate'),
                self.request.link(self.model, name='duplicate'),
                attrs={'class': 'duplicate-link'}
            ),
            Link(
                _('Delete'),
                self.csrf_protected_url(
                    self.request.link(self.model)
                ),
                attrs={'class': 'delete-link'},
                traits=(
                    Confirm(
                        _('Do you really want to delete this course event ?'),
                        _('This cannot be undone.'),
                        _('Delete course event'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.request.link(
                            self.course_collection
                        )
                    )
                )
            ),
            LinkGroup(_('Manage'), links=(
                Link(
                    _('Email Templates'),
                    self.request.link(self.template_collection),
                    attrs={'class': 'email-link'}
                ),
            )),
            Link(
                _('Cancel Event'),
                self.csrf_protected_url(
                    self.request.link(self.model, name='cancel')
                ),
                attrs={'class': 'cancel-icon'},
                traits=(
                    Confirm(
                        _('Do you really want to cancel this course event ?'),
                        _('An email will be sent to all the subscribers'),
                        _('Cancel course event'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=self.request.link(
                            self.course_collection
                        )
                    )
                )
            ),
        ]

    @cached_property
    def intercooler_btn(self) -> Link:
        btn_class = f'button {"disabled" if self.model.booked else ""}'
        return Link(
            text=_('Subscribe'),
            url=self.csrf_protected_url(
                self.request.link(
                    SubscriptionsCollection(
                        self.request.session,
                        auth_attendee=self.request.attendee,
                        course_event_id=self.model.id,
                        attendee_id=self.request.attendee_id
                    ),
                    name='add-from-course-event'
                )
            ),
            attrs={'class': btn_class},
            traits=(
                Confirm(
                    _('Do you want to register for this course event ?'),
                    _('A confirmation email will be sent to you later.'),
                    _('Register for course event'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='POST',
                    redirect_after=self.request.class_link(
                        CourseCollection
                    )
                )
            )
        )


class EditCourseEventLayout(CourseEventLayout):

    @property
    def title(self) -> str:
        return _('Edit course event')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        breadcrumbs = super().breadcrumbs
        breadcrumbs.append(Link(_('Edit')))
        return breadcrumbs


class AddCourseEventLayout(CourseEventCollectionLayout):

    @property
    def title(self) -> str:
        return _('Add course event')

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return [
            Link(
                text=_('Add Course Event'),
                url=self.request.class_link(
                    CourseEventCollection, name='add'
                ),
                attrs={'class': 'add-icon'}
            ),
        ]

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        links.append(Link(_('Add')))
        return links


class DuplicateCourseEventLayout(CourseEventLayout):

    @property
    def title(self) -> str:
        return _('Duplicate course event')

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return [Link(_('Duplicate'), attrs={'class': 'copy-link'})]
