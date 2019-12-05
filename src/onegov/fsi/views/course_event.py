from onegov.core.security import Personal, Secret
from onegov.fsi import FsiApp
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.forms.course_event import CourseEventForm
from onegov.fsi import _
from onegov.fsi.layouts.course_event import EditCourseEventLayout, \
    DuplicateCourseEventLayout, AddCourseEventLayout, \
    CourseEventCollectionLayout, CourseEventLayout
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.views.notifcations import handle_send_email


@FsiApp.html(
    model=CourseEventCollection,
    template='course_events.pt',
    permission=Personal
)
def view_course_event_collection(self, request):
    layout = CourseEventCollectionLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'events': self.query().all()
    }


@FsiApp.form(
    model=CourseEventCollection,
    template='form.pt',
    name='add',
    form=CourseEventForm,
    permission=Secret
)
def view_add_course_event(self, request, form):
    layout = AddCourseEventLayout(self, request)

    if form.submitted(request):
        course_event = self.add(**form.get_useful_data())
        request.success(_("Added a new course event"))
        return request.redirect(request.link(course_event))

    return {
        'layout': layout,
        'model': self,
        'form': form
    }


@FsiApp.html(
    model=CourseEvent,
    template='course_event.pt',
    permission=Personal
)
def view_course_event(self, request):
    layout = CourseEventLayout(self, request)
    return {
        'layout': layout,
        'model': self,
    }


@FsiApp.form(
    model=CourseEvent,
    template='form.pt',
    name='edit',
    form=CourseEventForm,
    permission=Secret
)
def view_edit_course_event(self, request, form):
    layout = EditCourseEventLayout(self, request)

    if form.submitted(request):
        form.update_model(self)

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'model': self,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.form(
    model=CourseEvent,
    template='form.pt',
    name='duplicate',
    form=CourseEventForm,
    permission=Secret
)
def view_duplicate_course_event(self, request, form):
    layout = DuplicateCourseEventLayout(self, request)

    if form.submitted(request):
        duplicate = CourseEventCollection(
            request.session).add(**form.get_useful_data())

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(duplicate))

    form.apply_model(self.duplicate)

    return {
        'layout': layout,
        'model': self,
        'form': form
    }


@FsiApp.view(
    model=CourseEvent,
    request_method='DELETE',
    permission=Secret
)
def delete_course_event(self, request):

    request.assert_valid_csrf_token()
    if not self.reservations.count():
        CourseEventCollection(request.session).delete(self)
    else:
        request.warning(_(
            'This event has registrations and can not be deleted'))


@FsiApp.view(
    model=CourseEvent,
    request_method='POST',
    permission=Secret,
    name='cancel'
)
def cancel_course_event(self, request):

    request.assert_valid_csrf_token()
    self.status = 'canceled'

    recipients = [a.id for a in self.attendees]

    if recipients:
        request = handle_send_email(
            self.cancellation_template,
            request,
            recipients,
            cc_to_sender=True
        )

        request.success(_(
            'Event cancelled and ${count} emails sent.',
            mapping={'count': self.attendees.count()}))
    else:
        request.warn('No recipients and no cancellation emails sent')
