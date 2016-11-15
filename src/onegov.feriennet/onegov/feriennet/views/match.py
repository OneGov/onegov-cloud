from onegov.core.security import Secret
from onegov.activity import Booking, BookingCollection
from onegov.activity.matching import deferred_acceptance_from_database
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.layout import MatchCollectionLayout


@FeriennetApp.html(
    model=MatchCollection,
    template='matches.pt',
    permission=Secret)
def view_matches(self, request):

    layout = MatchCollectionLayout(self, request)

    return {
        'layout': layout,
        'title': _("Matches for ${title}", mapping={
            'title': self.period.title
        }),
        'occasions': self.occasions
    }


@FeriennetApp.view(
    model=MatchCollection,
    name='ausfuehren',
    permission=Secret,
    request_method="POST")
def run_matching(self, request):
    assert self.period.active

    deferred_acceptance_from_database(request.app.session(), self.period_id)
    request.success(_("The matching run executed successfully"))


@FeriennetApp.view(
    model=MatchCollection,
    name='zuruecksetzen',
    permission=Secret,
    request_method="POST")
def reset_matching(self, request):
    assert self.period.active

    bookings = BookingCollection(request.app.session(), self.period_id)
    bookings.query().update({Booking.state: 'open'})

    request.success(_("The period was successfully reset"))
