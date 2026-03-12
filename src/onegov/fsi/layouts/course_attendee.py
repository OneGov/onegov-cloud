from __future__ import annotations

from functools import cached_property

from onegov.core.elements import Link, LinkGroup, Confirm, Intercooler
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.subscription import SubscriptionsCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.models import CourseAttendee


class CourseAttendeeCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        if self.request.view_name == 'add-external':
            return _('Add External Attendee')
        return _('Manage Course Attendees')

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        if not self.request.is_manager:
            return []
        return [
            Link(
                _('Add External Attendee'),
                url=self.request.class_link(
                    CourseAttendeeCollection, name='add-external'),
                attrs={'class': 'add-external'}
            ),
        ]

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(_('Manage Course Attendees'), self.request.link(self.model))
        )
        if self.request.view_name == 'add-external':
            links.append(Link(_('Add External Attendee')))
        return links

    @cached_property
    def collection(self) -> CourseAttendeeCollection:
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.attendee
        )

    @cached_property
    def collection_externals(self) -> CourseAttendeeCollection:
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.attendee,
            external_only=True
        )

    @cached_property
    def collection_editors(self) -> CourseAttendeeCollection:
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.attendee,
            editors_only=True
        )

    @cached_property
    def collection_admins(self) -> CourseAttendeeCollection:
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.attendee,
            admins_only=True
        )

    @cached_property
    def menu(self) -> list[tuple[str, str, bool]]:
        if not self.request.is_admin:
            # Hide menu for editor since filtered by permissions
            return []
        return [
            (_('All'), self.request.link(self.collection),
             self.model.unfiltered),
            (_('Editors'), self.request.link(self.collection_editors),
             self.model.editors_only),
            (_('Admins'), self.request.link(self.collection_admins),
             self.model.admins_only),
            (_('External'), self.request.link(self.collection_externals),
             self.model.external_only),
        ]


class CourseAttendeeLayout(DefaultLayout):

    model: CourseAttendee

    @cached_property
    def title(self) -> str:
        if self.request.view_name == 'edit':
            return _('Edit Profile')
        return _('Profile Details')

    @cached_property
    def collection(self) -> CourseAttendeeCollection:
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.attendee)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        if self.request.is_manager:
            links.append(
                Link(
                    _('Manage Course Attendees'),
                    self.request.link(self.collection)
                )
            )
        links.append(
            Link(_('Personal Profile'), self.request.link(self.model)))
        if self.request.view_name == 'edit':
            links.append(
                Link(_('Edit'), self.request.link(self.model, name='edit'))
            )
        return links

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []
        if self.request.is_manager:
            links = [
                Link(
                    _('Add Subscription'),
                    self.request.link(SubscriptionsCollection(
                        self.request.session, attendee_id=self.model.id,
                        auth_attendee=self.request.attendee),
                        name='add'),
                    attrs={'class': 'add-icon'}
                )
            ]
        if self.request.is_admin:
            links.append(
                Link(
                    _('Edit Profile'),
                    self.request.link(self.model, name='edit'),
                    attrs={'class': 'edit-link'}
                )
            )
            links.append(
                Link(
                    _('Add External Attendee'),
                    self.request.link(self.collection, name='add-external'),
                    attrs={'class': 'add-external'}
                )
            )
            if self.model.is_external:
                links.append(
                    Link(
                        _('Delete'),
                        self.csrf_protected_url(
                            self.request.link(self.model)
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Confirm(
                                _('Do you really want to delete '
                                  'this external attendee ?'),
                                _('This cannot be undone.'),
                                _('Delete external attendee'),
                                _('Cancel')
                            ),
                            Intercooler(
                                request_method='DELETE',
                                redirect_after=self.request.link(
                                    self.collection
                                )
                            )
                        )
                    )
                )
        return links

    @property
    def for_himself(self) -> bool:
        if self.request.attendee is None:
            return False
        return self.model.id == self.request.attendee.id
