from onegov.core.security import Personal, Public

from onegov.org.views.userprofile import handle_user_profile, \
    handle_unsubscribe
from onegov.town6.app import TownApp
from onegov.org.forms import UserProfileForm
from onegov.org.models import Organisation
from onegov.town6.layout import DefaultLayout


@TownApp.form(
    model=Organisation, name='userprofile', template='userprofile.pt',
    permission=Personal, form=UserProfileForm)
def town_handle_user_profile(self, request, form):
    return handle_user_profile(
        self, request, form, DefaultLayout(self, request))


# the view name must remain english, so that automated tools can detect it
@TownApp.html(
    model=Organisation,
    name='unsubscribe',
    template='userprofile.pt',
    permission=Public
)
def town_handle_unsubscribe(self, request):
    """ Returns a redirect, no layout passed """
    return handle_unsubscribe(self, request)
