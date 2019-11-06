from onegov.fsi import FsiApp
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.forms.course import CourseForm
from onegov.fsi import _
from onegov.fsi.layout import CourseLayout


@FsiApp.html(
    model=CourseCollection,
    template='course_collection.pt')
def view_course_collection(self, request):
    layout = CourseLayout(self, request)
    return {
            'title': _('Courses'),
            'layout': layout,
            'model': self,
            'courses': self.query().all()
    }


@FsiApp.form(
    model=CourseCollection,
    template='form.pt',
    name='new',
    form=CourseForm
)
def view_create_course(self, request, form):
    layout = CourseLayout(self, request)

    if form.submitted(request):
        self.add(**form.get_useful_data())

        request.success(_("Added a new course"))
        return request.redirect(request.link(self))

    return {
        'title': _('Add Course'),
        'layout': layout,
        'model': self,
        'form': form

    }
