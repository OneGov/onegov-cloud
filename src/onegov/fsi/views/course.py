from onegov.fsi import FsiApp
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.forms.course import EditCourseForm
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


@FsiApp.html(
    model=CourseCollection,
    template='course_collection.pt')
def view_course_collection(self, request):
    layout = DefaultLayout(self, request)
    return {
            'title': _('Courses'),
            'layout': layout,
            'model': self,
            'courses': self.query().all()
    }

#
# @FsiApp.form(
#     model=CourseCollection,
#     template='course_collection.pt',
#     name='new',
#     form=EditCourseForm
# )
# def view_create_course(self, request, form):
#     layout = DefaultLayout(self, request)
#     return {
#         'title': _('Create Course'),
#         'layout': layout,
#         'model': self,
#         'form': form
#
#     }
