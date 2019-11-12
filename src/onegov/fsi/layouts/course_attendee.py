from cached_property import cached_property

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


class CourseAttendeeLayout(DefaultLayout):

    @cached_property
    def title(self):
        if self.request.view_name == '':
            return _('Profile Details')
        if self.request.view_name == 'edit':
            return _('Edit Profile')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(
            Link(_('Personal Profile'), self.request.link(self.model)))
        if self.request.view_name == 'edit':
            links.append(
                Link(_('Edit'), self.request.link(self.model, name='edit'))
            )
        return links

    @cached_property
    def editbar_links(self):
        if self.request.view_name == '':
            return [
                Link(
                    _('Edit Profile'),
                    url=self.request.link(self.model, name='edit'),
                    attrs={'class': 'edit-icon'}
                )
            ]
        if (self.request.view_name in ('add-external', 'edit')
                and self.request.is_manager):
            return [
                Link(
                    _('Add External Attendee'),
                    url=self.request.class_link(
                        CourseAttendeeCollection, name='add-external'),
                    attrs={'class': 'plus-icon'}
                )
            ]
        else:
            return []

    @cached_property
    def salutation(self):
        return self.format_salutation(self.model.title)


class CourseAttendeeCollectionLayout(CourseAttendeeLayout):

    @cached_property
    def collection(self):
        return CourseAttendeeCollection(self.request.session)

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
        if self.request.view_name == 'add-external':
            return [Link(_('Add External Attendee'))]
        else:
            return [Link(_('Personal Profile'))]
