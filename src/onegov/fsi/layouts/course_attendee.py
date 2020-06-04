from cached_property import cached_property

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


class CourseAttendeeCollectionLayout(DefaultLayout):

    @cached_property
    def title(self):
        if self.request.view_name == 'add-external':
            return _('Add External Attendee')
        return _('Manage Course Attendees')

    @cached_property
    def editbar_links(self):
        if not self.request.is_admin:
            return []
        return [
            Link(
                _('Add External Attendee'),
                url=self.request.class_link(
                    CourseAttendeeCollection, name='add-external'),
                attrs={'class': 'users'}
            ),
        ]

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(
            Link(_('Manage Course Attendees'), self.request.link(self.model))
        )
        if self.request.view_name == 'add-external':
            links.append(Link(_('Add External Attendee')))
        return links

    @cached_property
    def collection(self):
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.current_attendee
        )

    @cached_property
    def collection_externals(self):
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.current_attendee,
            external_only=True
        )

    @cached_property
    def collection_editors(self):
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.current_attendee,
            editors_only=True
        )

    @cached_property
    def collection_admins(self):
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.current_attendee,
            admins_only=True
        )

    @cached_property
    def menu(self):
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

    @cached_property
    def title(self):
        if self.request.view_name == 'edit':
            return _('Edit Profile')
        return _('Profile Details')

    @cached_property
    def collection(self):
        return CourseAttendeeCollection(
            self.request.session, auth_attendee=self.request.current_attendee)

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
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
    def editbar_links(self):
        links = []
        if self.request.is_manager:
            links = [
                Link(
                    _('Add Subscription'),
                    self.request.link(ReservationCollection(
                        self.request.session, attendee_id=self.model.id,
                        auth_attendee=self.request.current_attendee),
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
                                _("Do you really want to delete "
                                  "this external attendee ?"),
                                _("This cannot be undone."),
                                _("Delete external attendee"),
                                _("Cancel")
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
    def for_himself(self):
        return self.model.id == self.request.current_attendee.id
