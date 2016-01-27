""" The settings view, defining things like the logo or color of the town. """

import morepath

from onegov.core.security import Private, Public
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.forms import UserProfileForm
from onegov.town.layout import DefaultLayout
from onegov.town.models import Town
from onegov.user import UserCollection
from webob.exc import HTTPForbidden


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
        'initials': user.initials,
        'role': user.role
    }


# the view name must remain english, so that automated tools can detect it
@TownApp.html(model=Town, name='unsubscribe', template='userprofile.pt',
              permission=Public)
def handle_unsubscribe(self, request):
    """ Unsubscribes a user from all *regular* e-mails.

    To be able to use this method, an url has to be created like this::

        '{}?token={}'.format((
            request.link(town, name='unsubscribe'),
            request.new_url_safe_token(
                {'user': 'user@example.org'}, 'unsubscribe'
            )
        ))

    """

    # tokens are valid for 30 days
    max_age = 60 * 60 * 24 * 30
    salt = 'unsubscribe'
    newsletters = {
        'daily_ticket_statistics'
    }

    data = request.load_url_safe_token(
        request.params.get('token'), max_age=max_age, salt=salt
    )

    if not data:
        return HTTPForbidden()

    user = UserCollection(request.app.session()).by_username(data['user'])

    if not user:
        return HTTPForbidden()

    if not user.data:
        user.data = {}

    for newsletter in newsletters:
        user.data[newsletter] = False

    request.success(
        _("You have been successfully unsubscribed from all regular emails.")
    )
    return morepath.redirect(request.link(self))
