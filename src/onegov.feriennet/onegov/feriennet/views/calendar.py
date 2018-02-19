from morepath.request import Response
from onegov.core.security import Public
from onegov.feriennet import FeriennetApp
from onegov.feriennet.models import AttendeeCalendar


@FeriennetApp.view(
    model=AttendeeCalendar,
    permission=Public)
def view_attendee_calendar(self, request):
    return Response(
        self.calendar(request),
        content_type='text/calendar',
        content_disposition=f'inline; filename={self.name}.ics'
    )
