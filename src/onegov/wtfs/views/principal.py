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


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.core.types import RenderData
    from webob import Response as BaseResponse


@WtfsApp.html(
    model=Principal,
    template='home.pt',
    permission=Public
)
def view_home(
    self: Principal,
    request: 'CoreRequest'
) -> 'BaseResponse | RenderData':
    """ The home page. """

    layout = DefaultLayout(self, request)

    if not request.is_logged_in:
        assert layout.login_url is not None
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
def view_dispatch_dates(
    self: Principal,
    request: 'CoreRequest',
    form: MunicipalityIdSelectionForm
) -> Response | str:
    """ Show dispatches dates for a given municipality. """

    if form.submitted(request):
        layout = DefaultLayout(self, request)
        assert form.municipality is not None
        dates = [
            r.date for r in form.municipality.pickup_dates.filter(
                PickupDate.date > date.today()
            )
        ] or [date(2018, 1, 1), date.today()]
        return render_macro(
            layout.macros['dispatch_dates'],
            request,
            {'dates': dates, 'layout': layout}
        )

    return Response()
