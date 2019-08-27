from datetime import date
from morepath import Response
from onegov.core.security import Public
from onegov.core.templates import render_macro
from onegov.wtfs import WtfsApp
from onegov.wtfs.forms import MunicipalityIdSelectionForm
from onegov.wtfs.layouts import DefaultLayout
from onegov.wtfs.models import PickupDate
from onegov.wtfs.models import Principal
from onegov.wtfs.security import ViewModel


@WtfsApp.html(
    model=Principal,
    template='home.pt',
    permission=Public
)
def view_home(self, request):
    """ The home page. """

    layout = DefaultLayout(self, request)

    if not request.is_logged_in:
        return request.redirect(layout.login_url)

    if not layout.notifications.query().first():
        return request.redirect(layout.top_navigation[0].attrs['href'])

    return {'layout': layout}


@WtfsApp.form(
    model=Principal,
    permission=ViewModel,
    name='dispatch-dates',
    form=MunicipalityIdSelectionForm
)
def view_dispatch_dates(self, request, form):
    """ Show dispatches dates for a given municipality. """

    if form.submitted(request):
        layout = DefaultLayout(self, request)
        dates = [
            r.date for r in form.municipality.pickup_dates.filter(
                PickupDate.date > date.today()
            )
        ]
        return render_macro(
            layout.macros['dispatch_dates'],
            request,
            {'dates': dates, 'layout': layout}
        )

    return Response()
