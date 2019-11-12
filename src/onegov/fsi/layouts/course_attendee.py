from cached_property import cached_property

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.fsi.collections.attendee import CourseAttendeeCollection
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
            Link(_('Manage Attendees'), self.request.link(self.model))
        )
        if self.request.view_name == 'add-external':
            links.append(Link(_('Add External Attendee')))
        return links


class CourseAttendeeLayout(DefaultLayout):

    @cached_property
    def title(self):
        if self.request.view_name == 'edit':
            return _('Edit Profile')
        return _('Profile Details')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        if self.request.is_manager:
            links.append(
                Link(
                    _('Manage Attendees'),
                    self.request.class_link(CourseAttendeeCollection)
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
        links = [Link(
            _('Edit Profile'),
            url=self.request.link(self.model, name='edit'),
            attrs={'class': 'edit-icon'}
        )]
        if self.request.is_manager:
            links.append(
                Link(
                    _('Add External Attendee'),
                    url=self.request.class_link(
                        CourseAttendeeCollection, name='add-external'),
                    attrs={'class': 'plus-icon'}
                )
            )
        return links

    @cached_property
    def salutation(self):
        return self.format_salutation(self.model.title)