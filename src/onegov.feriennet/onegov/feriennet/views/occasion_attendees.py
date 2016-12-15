from onegov.core.security import Private
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.layout import OccasionAttendeeLayout
from onegov.feriennet.views.shared import all_periods


@FeriennetApp.html(
    model=OccasionAttendeeCollection,
    template='occasion_attendees.pt',
    permission=Private)
def view_occasion_attendees(self, request):

    return {
        'layout': OccasionAttendeeLayout(self, request),
        'title': _("Attendees for ${period}", mapping={
            'period': self.period.title
        }),
        'occasions': self.occasions(),
        'periods': all_periods(request),
        'period': self.period,
        'model': self
    }
