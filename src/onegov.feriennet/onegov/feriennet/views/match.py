from onegov.core.security import Secret
from onegov.activity import BookingCollection, Occasion
from onegov.activity.matching import deferred_acceptance_from_database
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.forms import MatchForm
from onegov.feriennet.layout import MatchCollectionLayout
from onegov.feriennet.views.shared import all_periods


@FeriennetApp.form(
    model=MatchCollection,
    form=MatchForm,
    template='matches.pt',
    permission=Secret)
def handle_matches(self, request, form):

    layout = MatchCollectionLayout(self, request)

    if form.submitted(request):
        assert self.period.active and not self.period.confirmed

        deferred_acceptance_from_database(
            session=request.app.session(),
            period_id=self.period_id,
            score_function=form.scoring(request.app.session()))

        self.period.scoring = form.scoring(request.app.session())

        if form.confirm_period:
            self.period.confirm()
            request.success(_("The matching was confirmed successfully"))
        else:
            request.success(_("The matching run executed successfully"))

    elif not request.POST:
        form.process_scoring(self.period.scoring)

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
        'period': self.period,
        'periods': all_periods(request),
        'form': form,
        'button_text': _("Run Matching"),
        'model': self
    }


@FeriennetApp.view(
    model=MatchCollection,
    name='zuruecksetzen',
    permission=Secret,
    request_method="POST")
def reset_matching(self, request):
    assert self.period.active and not self.period.confirmed

    bookings = BookingCollection(request.app.session(), self.period_id)
    for booking in bookings.query():
        booking.state = 'open'

    request.success(_("The period was successfully reset"))
