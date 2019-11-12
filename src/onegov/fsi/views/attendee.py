from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi import _
from onegov.fsi.forms.course_attendee import CourseAttendeeForm, \
    ExternalCourseAttendeeForm
from onegov.fsi.layouts.course_attendee import CourseAttendeeLayout, \
    CourseAttendeeCollectionLayout
from onegov.fsi.models.course_attendee import CourseAttendee


@FsiApp.html(
    model=CourseAttendeeCollection,
    request_method='POST',
    name='add-from-user',
)
def view_add_attendee_from_user(self, request):
    if not request.current_user.attendee:
        self.add_from_user(request.current_user)
        request.success(_("Added attendee linked to your user"))
    else:
        request.info(_('Attendee already existed'))
    # return request.redirect(request.link(self))


@FsiApp.html(model=CourseAttendeeCollection, template='course_attendees.pt')
def view_course_attendee_collection(self, request):
    layout = CourseAttendeeCollectionLayout(self, request)
    return {
        'title': layout.title,
        'layout': layout,
        'attendees': self.query().all(),
    }


@FsiApp.html(model=CourseAttendee, template='course_attendee.pt')
def view_course_attendee(self, request):
    layout = CourseAttendeeLayout(self, request)
    return {
        'title': layout.title,
        'layout': layout,
        'model': self,
    }


@FsiApp.form(model=CourseAttendee, name='edit', form=CourseAttendeeForm,
             template='form.pt')
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


@FsiApp.form(model=CourseAttendeeCollection, template='form.pt',
             form=ExternalCourseAttendeeForm, name='add-external')
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
