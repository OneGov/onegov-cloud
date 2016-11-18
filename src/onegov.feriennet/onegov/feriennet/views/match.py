from onegov.core.security import Secret
from onegov.activity import Booking, BookingCollection, Occasion
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

    def activity_link(oid):
        return request.class_link(Occasion, {'id': oid})

    return {
        'layout': layout,
        'title': _("Matches for ${title}", mapping={
            'title': self.period.title
        }),
        'occasions': self.occasions,
        'activity_link': activity_link,
        'happiness': '{}%'.format(round(self.happiness * 100)),
        'operability': '{}%'.format(round(self.operability * 100)),
        'period': self.period
    }


@FeriennetApp.view(
    model=MatchCollection,
    name='ausfuehren',
    permission=Secret,
    request_method="POST")
def run_matching(self, request):
    assert self.period.active and not self.period.confirmed

    deferred_acceptance_from_database(request.app.session(), self.period_id)
    request.success(_("The matching run executed successfully"))


@FeriennetApp.view(
    model=MatchCollection,
    name='zuruecksetzen',
    permission=Secret,
    request_method="POST")
def reset_matching(self, request):
    assert self.period.active and not self.period.confirmed

    bookings = BookingCollection(request.app.session(), self.period_id)
    bookings.query().update({Booking.state: 'open'})

    request.success(_("The period was successfully reset"))
