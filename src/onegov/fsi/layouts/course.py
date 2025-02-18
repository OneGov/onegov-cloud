from __future__ import annotations

from functools import cached_property

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.fsi.collections.audit import AuditCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.layout import DefaultLayout, FormatMixin
from onegov.fsi import _
from onegov.org.elements import LinkGroup

from onegov.org.layout import DefaultMailLayout as OrgDefaultMailLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.templates import MacrosLookup
    from onegov.core.types import RenderData
    from onegov.fsi.app import FsiApp
    from onegov.fsi.models import Course
    from onegov.fsi.request import FsiRequest


class CourseInviteMailLayout(OrgDefaultMailLayout, FormatMixin):
    """Takes a course as its model, not a notification template """

    app: FsiApp
    request: FsiRequest
    model: Course

    @cached_property
    def event_collection(self) -> CourseEventCollection:
        return CourseEventCollection(
            self.request.session, course_id=self.model.id, upcoming_only=True)

    @cached_property
    def default_macros(self) -> MacrosLookup:
        return self.template_loader.macros

    @cached_property
    def event_collection_url(self) -> str:
        return self.request.link(self.event_collection)

    @cached_property
    def course_url(self) -> str:
        return self.request.link(self.model)

    @cached_property
    def upcoming_events_collection(self) -> CourseEventCollection:
        return CourseEventCollection(
            self.request.session,
            course_id=self.model.id,
            upcoming_only=True)

    @cached_property
    def open_events_url(self) -> str:
        return self.request.link(self.upcoming_events_collection)

    @property
    def notification_type(self) -> str:
        return 'invitation'


class CourseCollectionLayout(DefaultLayout):

    @property
    def title(self) -> str:
        return _('Courses')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        """ Returns the breadcrumbs for the current page. """
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(
                self.title,
                self.request.class_link(CourseCollection)))
        return links

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []
        if self.request.is_admin:
            links.append(
                Link(
                    text=_('New Course'),
                    url=self.request.class_link(
                        CourseCollection, name='add'
                    ),
                    attrs={'class': 'add-icon'}
                )
            )

        return links

    def accordion_items(
        self,
        upcoming_only: bool = True
    ) -> list[RenderData]:

        assert self.request.attendee is not None
        coll = CourseEventCollection(
            self.request.session,
            upcoming_only=upcoming_only,
            show_hidden=self.request.attendee.role == 'admin',
            sort_desc=True
        )
        result: list[RenderData] = []
        for course in self.model.query():
            coll.course_id = course.id
            result.append({
                'title': course.name,
                'content': course.description,
                'listing_url': self.request.link(coll, name='as-listing'),
                'url': self.request.link(course),
            })
        return result


class CourseLayout(CourseCollectionLayout):

    model: Course

    @cached_property
    def audit_collection(self) -> AuditCollection:
        assert self.request.attendee is not None
        return AuditCollection(
            self.request.session, self.model.id, self.request.attendee)

    @cached_property
    def event_collection(self) -> CourseEventCollection:
        return CourseEventCollection(
            self.request.session, course_id=self.model.id)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        """ Returns the breadcrumbs for the detail page. """
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(self.model.name, self.request.link(self.model))
        )
        return links

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        if not self.request.is_manager:
            return []

        links: list[Link | LinkGroup] = [
            Link(
                _('Audit'),
                self.request.link(self.audit_collection),
                attrs={'class': 'audit-icon'}
            )
        ]

        if self.request.is_editor:
            return links

        links.extend(
            [
                LinkGroup(
                    title=_('Add'),
                    links=(
                        Link(
                            _('Event'),
                            self.request.link(self.event_collection,
                                              name='add'),
                            attrs={'class': 'new-event'}
                        ),
                    )
                ),
                Link(
                    _('Edit'),
                    self.request.link(self.model, name='edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    _('Delete'),
                    self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete this course ?'),
                            _('This cannot be undone.'),
                            _('Delete course'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                CourseCollection
                            )
                        )
                    )
                )
            ]
        )
        return links


class AddCourseLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        breadcrumbs = super().breadcrumbs
        assert isinstance(breadcrumbs, list)
        breadcrumbs.append(
            Link(_('Courses'), self.request.class_link(CourseCollection))
        )
        breadcrumbs.append(Link(_('Add')))
        return breadcrumbs

    @property
    def title(self) -> str:
        return _('New Course')


class EditCourseLayout(DefaultLayout):

    model: Course

    @property
    def title(self) -> str:
        return _('Edit Course')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        breadcrumbs = super().breadcrumbs
        assert isinstance(breadcrumbs, list)
        breadcrumbs.append(
            Link(_('Courses'), self.request.class_link(CourseCollection))
        )
        breadcrumbs.append(
            Link(self.model.name, self.request.link(self.model))
        )
        breadcrumbs.append(Link(_('Edit')))
        return breadcrumbs


class InviteCourseLayout(DefaultLayout):

    model: Course

    @property
    def title(self) -> str:
        return _('Invite Attendees')

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return []

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        bread = super().breadcrumbs
        assert isinstance(bread, list)
        bread.append(
            Link(_('Courses'), self.request.class_link(CourseCollection))
        )
        bread.append(
            Link(self.model.name, self.request.link(self.model))
        )
        bread.append(
            Link(_('Invite Attendees'))
        )
        return bread
