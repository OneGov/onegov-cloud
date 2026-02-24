from __future__ import annotations

from morepath.request import Response
from onegov.core.security import Public
from onegov.feriennet import FeriennetApp
from onegov.feriennet.models import AttendeeCalendar


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest


@FeriennetApp.view(
    model=AttendeeCalendar,
    permission=Public)
def view_attendee_calendar(
    self: AttendeeCalendar,
    request: FeriennetRequest
) -> Response:
    return Response(
        self.calendar(request),
        content_type='text/calendar',
        content_disposition=f'inline; filename={self.name}.ics'
    )
