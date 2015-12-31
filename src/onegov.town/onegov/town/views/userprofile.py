""" The settings view, defining things like the logo or color of the town. """

from onegov.core.security import Private
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.forms import UserProfileForm
from onegov.town.layout import DefaultLayout
from onegov.town.models import Town
from onegov.user import UserCollection


@TownApp.form(
    model=Town, name='benutzerprofil', template='userprofile.pt',
    permission=Private, form=UserProfileForm)
def handle_user_profile(self, request, form):
    """ Handles the GET and POST login requests. """

    layout = DefaultLayout(self, request)

    collection = UserCollection(request.app.session())
    user = collection.by_username(request.identity.userid)

    if form.submitted(request):
        form.update_model(user)
        request.success(_("Your changes were saved"))
    else:
        form.apply_model(user)

    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("User Profile"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _("User Profile"),
        'form': form,
        'username': user.username,
        'role': user.role
    }
