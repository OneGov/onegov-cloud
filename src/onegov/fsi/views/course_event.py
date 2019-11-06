from onegov.fsi import FsiApp
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.layout import CourseEventsLayout


# @FsiApp.form(
#     model=CourseEventCollection,
#     template='form.pt',
#     name='new',
#     form=CourseEventForm
# )
# def view_create_course(self, request, form):
#     layout = CourseEventsLayout(self, request)
#     return {
#         'title': _('Add Course'),
#         'layout': layout,
#         'model': self,
#         'form': form
#     }
