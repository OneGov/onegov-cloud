from cached_property import cached_property

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _
from onegov.org.elements import LinkGroup


class CourseCollectionLayout(DefaultLayout):
    @cached_property
    def title(self):
        return _('Courses')

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        links = super().breadcrumbs
        links.append(
            Link(
                self.title,
                self.request.class_link(CourseCollection)))
        return links

    @cached_property
    def editbar_links(self):
        links = []
        if self.request.is_manager:
            links.append(
                Link(
                    text=_("New Course"),
                    url=self.request.class_link(
                        CourseCollection, name='add'
                    ),
                    attrs={'class': 'add-icon'}
                )
            )

        return links

    @property
    def accordion_items(self):
        return tuple(
            dict(
                title=c.name,
                content=c.description,
                url=self.request.link(c),
                edit_url=self.request.link(c, name='edit'),
                events_url=self.request.link(
                    CourseEventCollection(
                        self.request.session,
                        course_id=c.id,
                        upcoming_only=True
                    )
                )
            ) for c in self.model.query()
        )


class CourseLayout(CourseCollectionLayout):

    @cached_property
    def event_collection(self):
        return CourseEventCollection(
            self.request.session, course_id=self.model.id)

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the detail page. """
        links = super().breadcrumbs
        links.append(
            Link(self.model.name, self.request.link(self.model))
        )
        return links

    @cached_property
    def editbar_links(self):
        if not self.request.is_manager:
            return []
        return [
            LinkGroup(
                title=_('Add'),
                links=(
                    Link(
                        _('Event'),
                        self.request.link(self.event_collection, name='add'),
                        attrs={'class': 'new-event'}
                    ),
                )
            ),
            Link(
                _('Invite Attendees'),
                self.request.link(self.model, name='invite'),
                attrs={'class': 'invite-attendees'}
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
                        _("Do you really want to delete this course ?"),
                        _("This cannot be undone."),
                        _("Delete course"),
                        _("Cancel")
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.request.class_link(
                            CourseCollection
                        )
                    )
                )
            ),
        ]


class AddCourseLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        breadcrumbs = super().breadcrumbs
        breadcrumbs.append(
            Link(_('Courses'), self.request.class_link(CourseCollection))
        )
        breadcrumbs.append(Link(_('Add')))
        return breadcrumbs

    @cached_property
    def title(self):
        return _('New Course')


class EditCourseLayout(DefaultLayout):
    @cached_property
    def title(self):
        return _('Edit Course')

    @cached_property
    def breadcrumbs(self):
        breadcrumbs = super().breadcrumbs
        breadcrumbs.append(
            Link(_('Courses'), self.request.class_link(CourseCollection))
        )
        breadcrumbs.append(
            Link(self.model.name, self.request.link(self.model))
        )
        breadcrumbs.append(Link(_('Edit')))
        return breadcrumbs


class InviteCourseLayout(CourseLayout):

    @cached_property
    def title(self):
        return _('Invite Attendees')

    @cached_property
    def editbar_links(self):
        return []

    @cached_property
    def breadcrumbs(self):
        bread = super().breadcrumbs
        bread.append(
            Link(_('Invite Attendees'))
        )
        return bread
