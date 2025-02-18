from __future__ import annotations

from onegov.core.security import Private
from onegov.activity import OccasionNeed, Volunteer
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.layout import OccasionAttendeeLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.activity.models import Occasion
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest


@FeriennetApp.html(
    model=OccasionAttendeeCollection,
    template='occasion_attendees.pt',
    permission=Private)
def view_occasion_attendees(
    self: OccasionAttendeeCollection,
    request: FeriennetRequest
) -> RenderData:

    def occasion_volunteers(occasion: Occasion) -> tuple[Volunteer, ...]:
        return tuple(request.session.query(Volunteer).join(OccasionNeed).
                     filter(OccasionNeed.occasion_id == occasion.id).
                     filter(Volunteer.state == 'confirmed').
                     order_by(Volunteer.first_name, Volunteer.last_name))
    return {
        'layout': OccasionAttendeeLayout(self, request),
        'title': _('Attendees for ${period}', mapping={
            'period': self.period.title
        }),
        'occasions': self.occasions(),
        'occasion_volunteers': occasion_volunteers,
        'periods': request.app.periods,
        'period': self.period,
        'model': self,
        'organisation': request.app.org,
    }
