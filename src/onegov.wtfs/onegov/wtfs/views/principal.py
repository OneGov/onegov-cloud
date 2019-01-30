from onegov.core.security import Public
from onegov.wtfs import WtfsApp
from onegov.wtfs.layouts import DefaultLayout
from onegov.wtfs.models import Principal


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

    return {
        'layout': layout
    }
