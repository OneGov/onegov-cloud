from cached_property import cached_property

from onegov.core.elements import Link, Confirm, Intercooler
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _
from onegov.fsi.models.course_event import (
    COURSE_EVENT_STATUSES_TRANSLATIONS, COURSE_EVENT_STATUSES
)


class CourseEventLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _('Course Event Details')

    @cached_property
    def collection(self):
        return CourseEventCollection(
            self.request.session,
        )

    @cached_property
    def reservation_collection(self):
        return ReservationCollection(
            self.request.session,
            attendee_id=self.request.attendee_id,
            course_event_id=self.model.id
        )

    @cached_property
    def collection_url(self):
        return self.request.class_link(CourseEventCollection)

    @cached_property
    def editbar_links(self):
        if not self.request.is_manager:
            return []
        return [
            Link(
                text=_("Add Course Event"),
                url=self.request.class_link(
                    CourseEventCollection, name='add'
                ),
                attrs={'class': 'add-icon'}
            ),
            Link(
                text=_("Edit"),
                url=self.request.link(self.model, name='edit'),
                attrs={'class': 'edit-icon'}
            ),
            Link(
                text=_('Duplicate'),
                url=self.request.link(self.model, name='duplicate'),
                attrs={'class': 'new-link'}
            ),
            Link(
                text=_("Delete"),
                url=self.csrf_protected_url(
                    self.request.link(self.model)
                ),
                attrs={'class': 'delete-link'},
                traits=(
                    Confirm(
                        _("Do you really want to delete this course event ?"),
                        _("This cannot be undone."),
                        _("Delete course event"),
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
        ]

    @cached_property
    def confirmation_btn(self):
        btn_class = f'button {"disabled" if self.model.booked else ""}'
        return Link(
                text=_("Make Reservation"),
                url=self.csrf_protected_url(
                    self.request.link(
                        self.reservation_collection,
                        name='add-from-course-event'
                    )
                ),
                attrs={'class': btn_class},
                traits=(
                    Confirm(
                        _("Do you want to register for this course event ?"),
                        _("A confirmation email will be sent to you later."),
                        _("Register for course event"),
                        _("Cancel")
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=self.request.class_link(
                            ReservationCollection
                        )
                    )
                )
            )


class CourseEventCollectionLayout(CourseEventLayout):

    @cached_property
    def title(self):
        if self.model.limit:
            return _('Upcoming Course Events')
        return _('Course Events')

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        links = [Link(_("Homepage"), self.homepage_url)]
        if self.request.is_manager:
            links.append(
                Link(_('Course management',
                       self.request.class_link(CourseEventCollection))))
        else:
            links.append(
                Link(_('Courses',
                       self.request.class_link(CourseEventCollection))))
        return links

    @cached_property
    def editbar_links(self):
        links = []
        if self.request.is_manager:
            links.append(
                Link(
                    text=_("Add Course Event"),
                    url=self.request.class_link(
                        CourseEventCollection, name='add'
                    ),
                    attrs={'class': 'add-icon'}
                )
            )

        return links


class EditCourseEventLayout(CourseEventLayout):

    @cached_property
    def title(self):
        return _('Edit course event')


class AddCourseEventLayout(CourseEventLayout):
    @cached_property
    def title(self):
        return _('Add course event')

    @cached_property
    def editbar_links(self):
        return [
            Link(
                text=_("Add Course Event"),
                url=self.request.class_link(
                    CourseEventCollection, name='add'
                ),
                attrs={'class': 'add-icon'}
            ),
        ]


class DuplicateCourseEventLayout(CourseEventLayout):
    @cached_property
    def title(self):
        return _('Duplicate course event')

    @cached_property
    def editbar_links(self):
        return [
            Link(
                text=_('Duplicate'),
                url='#',
                attrs={'class': 'copy-link'}
            )
        ]
