from onegov.fsi import FsiApp
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.layout import CourseEventsLayout


@FsiApp.html(model=CourseEventCollection, template='event_collection.pt')
def get_course_events_view(self, request):
    layout = CourseEventsLayout(self, request)
    return {
        'title': layout.title,
        'layout': layout,
        'events': self.query().all()
    }

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
