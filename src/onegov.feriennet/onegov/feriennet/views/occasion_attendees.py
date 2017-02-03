from onegov.core.security import Private
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.layout import OccasionAttendeeLayout


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
        'periods': request.app.periods,
        'period': self.period,
        'model': self
    }
