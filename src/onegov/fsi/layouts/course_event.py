from cached_property import cached_property

from onegov.core.elements import Link, Confirm, Intercooler, LinkGroup
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.notification_template import \
    FsiNotificationTemplateCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


class CourseEventCollectionLayout(DefaultLayout):

    @cached_property
    def title(self):
        if self.model.limit:
            return _('Upcoming Course Events')
        return _('Course Events')

    @cached_property
    def course_breadcrumbs_text(self):
        return _('Course management') if self.request.is_manager else _(
            'Courses')

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        links = super().breadcrumbs
        if self.request.is_manager:
            links.append(
                Link(
                    self.course_breadcrumbs_text,
                    self.request.class_link(CourseEventCollection)))
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


class CourseEventLayout(CourseEventCollectionLayout):

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
            course_event_id=self.model.id
        )

    @cached_property
    def template_collection(self):
        return FsiNotificationTemplateCollection(
            self.request.session,
            course_event_id=self.model.id
        )

    @cached_property
    def collection_url(self):
        return self.request.class_link(CourseEventCollection)

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the detail page. """
        links = super().breadcrumbs
        links.append(
            Link(_('Current Course Event'), self.request.link(self.model))
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
                        _('Duplicate'),
                        self.request.link(self.model, name='duplicate'),
                        attrs={'class': 'new-link'}
                    ),
                    Link(
                        _('Reservation for External'),
                        self.request.link(
                            ReservationCollection(
                                self.request.session,
                                course_event_id=self.model.id,
                                external_only=True),
                            name='add'
                        ),
                        attrs={'class': 'new-link'}
                    ),
                    Link(
                        _("Placeholder Reservation"),
                        self.request.link(
                            self.reservation_collection,
                            name='add-placeholder'
                        ),
                        attrs={'class': 'add-icon'}
                    ),
                    Link(
                        _("New Course Event"),
                        self.request.class_link(
                            CourseEventCollection, name='add'),
                        attrs={'class': 'add-icon'}
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
            ),
            LinkGroup(_('Manage'), links=(
                Link(_('Email Templates'), self.request.link(
                    self.template_collection)
                     ),
                Link(_('Reservations'),
                     self.request.link(self.reservation_collection))
            )),
        ]

    @cached_property
    def intercooler_btn(self):
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


class EditCourseEventLayout(CourseEventLayout):

    @cached_property
    def title(self):
        return _('Edit course event')

    @cached_property
    def breadcrumbs(self):
        breadcrumbs = super().breadcrumbs
        breadcrumbs.append(Link(_('Edit'), '#'))
        return breadcrumbs


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

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(_('Add'), '#'))
        return links


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
