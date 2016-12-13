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
        'title': _("Attendees"),
        'occasions': self.occasions()
    }
