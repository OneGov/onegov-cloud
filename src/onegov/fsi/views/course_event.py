from onegov.fsi import FsiApp
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.forms.course_event import CourseEventForm
from onegov.fsi import _
from onegov.fsi.layouts.course_event import EditCourseEventLayout, \
    DuplicateCourseEventLayout, AddCourseEventLayout, \
    CourseEventCollectionLayout, CourseEventLayout
from onegov.fsi.models.course_event import CourseEvent


@FsiApp.html(
    model=CourseEventCollection,
    template='course_events.pt')
def view_course_event_collection(self, request):
    layout = CourseEventCollectionLayout(self, request)
    return {
        'title': layout.title,
        'layout': layout,
        'model': self,
        'events': self.query().all()
    }


@FsiApp.form(
    model=CourseEventCollection,
    template='form.pt',
    name='new',
    form=CourseEventForm
)
def view_create_course_event(self, request, form):
    layout = AddCourseEventLayout(self, request)

    if form.submitted(request):
        self.add(**form.get_useful_data())

        request.success(_("Added a new course event"))
        return request.redirect(request.link(self))

    return {
        'title': layout.title,
        'layout': layout,
        'model': self,
        'form': form
    }


@FsiApp.html(
    model=CourseEvent,
    template='course_event.pt')
def view_course_event(self, request):
    layout = CourseEventLayout(self, request)
    return {
        'title': layout.title,
        'layout': layout,
        'model': self,
    }


@FsiApp.form(
    model=CourseEvent,
    template='form.pt',
    name='edit',
    form=CourseEventForm
)
def view_edit_course_event(self, request, form):
    layout = EditCourseEventLayout(self, request)
    layout.include_editor()

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
    model=CourseEvent,
    template='form.pt',
    name='duplicate',
    form=CourseEventForm
)
def view_duplicate_course_event(self, request, form):
    layout = DuplicateCourseEventLayout(self, request)

    if form.submitted(request):
        CourseEventCollection(
            request.session()).add(**form.get_useful_data())

        request.success(_("Your changes were saved"))
        return request.redirect(layout.collection_url)

    form.apply_model(self.duplicate)

    return {
        'title': layout.title,
        'layout': layout,
        'model': self,
        'form': form
    }


@FsiApp.view(
    model=CourseEvent,
    request_method='DELETE',
)
def delete_agency(self, request):

    request.assert_valid_csrf_token()
    CourseEventCollection(request.session).delete(self)