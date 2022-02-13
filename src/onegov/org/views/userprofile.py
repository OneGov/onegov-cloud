""" The settings of the logged in user. """

from morepath.request import Response
from onegov.core.security import Personal, Public
from onegov.org import _
from onegov.org.app import OrgApp
from onegov.org.elements import Link
from onegov.org.forms import UserProfileForm
from onegov.org.layout import DefaultLayout
from onegov.org.models import Organisation
from onegov.user import UserCollection
from webob.exc import HTTPForbidden


@OrgApp.form(
    model=Organisation, name='userprofile', template='userprofile.pt',
    permission=Personal, form=UserProfileForm)
def handle_user_profile(self, request, form, layout=None):
    """ Handles the GET and POST login requests. """

    layout = layout or DefaultLayout(self, request)

    collection = UserCollection(request.session)
    user = collection.by_username(request.identity.userid)

    if form.submitted(request):
        form.populate_obj(user)
        request.success(_("Your changes were saved"))

        if 'return-to' in request.GET:
            return request.redirect(request.link(self, 'userprofile'))

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


def unsubscribe(request):
    """ Unsubscribe a user from all *regular* e-mails.

    Returns True, if the request was valid.

    """

    # tokens are valid for 30 days
    max_age = 60 * 60 * 24 * 30
    salt = 'unsubscribe'
    newsletters = {'daily_ticket_statistics'}

    data = request.load_url_safe_token(
        request.params.get('token'), max_age=max_age, salt=salt
    )

    if data:
        user = UserCollection(request.session).by_username(data['user'])
        if user:
            if not user.data:
                user.data = {}
            for newsletter in newsletters:
                user.data[newsletter] = False
            return True

    return False


# the view name must remain english, so that automated tools can detect it
@OrgApp.html(model=Organisation, name='unsubscribe', template='unsubscribe.pt',
             permission=Public)
def handle_unsubscribe(self, request, layout=None):
    """ Unsubscribes a user from all *regular* e-mails.

    To be able to use this method, an url has to be created like this::

        '{}?token={}'.format((
            request.link(org, name='unsubscribe'),
            request.new_url_safe_token(
                {'user': 'user@example.org'}, 'unsubscribe'
            )
        ))

    This view never fails and always pretends to be successful.

    """

    if not unsubscribe(request):
        return HTTPForbidden()

    return {'layout': layout or DefaultLayout(self, request)}


# RFC-8058: respond to POST requests as well
@OrgApp.view(model=Organisation, name='unsubscribe', permission=Public,
             request_method='POST')
def handle_unsubscribe_rfc8058(self, request):
    # it doesn't really make sense to check for success here
    # since this is an automated action without verficiation
    unsubscribe(request)
    return Response()
