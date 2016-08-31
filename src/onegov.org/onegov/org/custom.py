from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.models import GeneralFileCollection, ImageFileCollection
from onegov.user.auth import Auth, UserCollection


@OrgApp.template_variables()
def get_template_variables(request):
    return {
        'bottom_links': tuple(get_bottom_links(request))
    }


def get_bottom_links(request):

    if request.is_logged_in:
        yield Link(_("Logout"), request.link(
            Auth.from_request_path(request), name='logout'))

        yield Link(_("User Profile"), request.link(
            request.app.org, name='benutzerprofil'))

    if request.is_manager:
        yield Link(_('Files'), request.class_link(
            GeneralFileCollection))

        yield Link(_('Images'), request.class_link(
            ImageFileCollection))

    if request.is_admin:
        yield Link(_('Settings'), request.link(
            request.app.org, 'einstellungen'))

        yield Link(_('Usermanagement'), request.class_link(
            UserCollection))

    if not request.is_logged_in:
        yield Link(_("Login"), request.link(
            Auth.from_request_path(request), name='login'))

        if request.app.settings.org.enable_user_registration:
            yield Link(_("Register"), request.link(
                Auth.from_request_path(request), name='register'
            ))

    yield Link('OneGov Cloud', 'http://www.onegovcloud.ch')
    yield Link('Seantis GmbH', 'https://www.seantis.ch')
