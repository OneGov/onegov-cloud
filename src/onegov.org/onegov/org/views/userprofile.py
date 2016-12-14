""" The settings of the logged in user. """

import morepath

from onegov.core.security import Personal, Public
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org import _
from onegov.org.app import OrgApp
from onegov.org.forms import UserProfileForm
from onegov.org.models import Organisation
from onegov.user import UserCollection
from webob.exc import HTTPForbidden


@OrgApp.form(
    model=Organisation, name='benutzerprofil', template='userprofile.pt',
    permission=Personal, form=UserProfileForm)
def handle_user_profile(self, request, form):
    """ Handles the GET and POST login requests. """

    layout = DefaultLayout(self, request)

    collection = UserCollection(request.app.session())
    user = collection.by_username(request.identity.userid)

    if form.submitted(request):
        form.populate_obj(user)
        request.success(_("Your changes were saved"))

        if 'return-to' in request.GET:
            return request.redirect(request.link(self, 'benutzerprofil'))

    elif not request.POST:
        form.process(obj=user)

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
@OrgApp.html(model=Organisation, name='unsubscribe', template='userprofile.pt',
             permission=Public)
def handle_unsubscribe(self, request):
    """ Unsubscribes a user from all *regular* e-mails.

    To be able to use this method, an url has to be created like this::

        '{}?token={}'.format((
            request.link(org, name='unsubscribe'),
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
