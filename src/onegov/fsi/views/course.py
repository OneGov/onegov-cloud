from onegov.fsi import FsiApp
from onegov.fsi.collections.course import CourseCollection
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
