from onegov.core.security import Private, Personal, Secret
from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi import _
from onegov.fsi.forms.course_attendee import CourseAttendeeForm, \
    AddExternalAttendeeForm
from onegov.fsi.layouts.course_attendee import CourseAttendeeLayout, \
    CourseAttendeeCollectionLayout
from onegov.fsi.models.course_attendee import CourseAttendee


@FsiApp.html(
    model=CourseAttendeeCollection,
    template='course_attendees.pt',
    permission=Private
)
def view_course_attendee_collection(self, request):
    layout = CourseAttendeeCollectionLayout(self, request)
    return {
        'title': layout.title,
        'layout': layout,
        'model': self
    }


@FsiApp.html(
    model=CourseAttendee,
    template='course_attendee.pt',
    permission=Personal
)
def view_course_attendee(self, request):
    layout = CourseAttendeeLayout(self, request)
    return {
        'title': layout.title,
        'layout': layout,
        'model': self,
    }


@FsiApp.form(
    model=CourseAttendee,
    name='edit',
    form=CourseAttendeeForm,
    template='form.pt',
    permission=Secret
)
def view_edit_course_attendee(self, request, form):
    layout = CourseAttendeeLayout(self, request)

    if form.submitted(request):

        form.update_model(self)

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'title': layout.title,
        'layout': layout,
        'model': self,
        'form': form
    }


@FsiApp.form(
    model=CourseAttendeeCollection,
    template='form.pt',
    form=AddExternalAttendeeForm,
    name='add-external',
    permission=Private
)
def view_att_external_attendee(self, request, form):
    layout = CourseAttendeeCollectionLayout(self, request)

    if form.submitted(request):
        attendee = self.add(**form.get_useful_data())
        request.success(_("Added a new course event"))
        return request.redirect(request.link(attendee))

    return {
        'title': layout.title,
        'layout': layout,
        'form': form
    }
