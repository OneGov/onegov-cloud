from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.models import GeneralFileCollection, ImageFileCollection
from onegov.user.auth import Auth


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

        yield Link(_('Files'), request.link(
            GeneralFileCollection(request.app)))

        yield Link(_('Images'), request.link(
            ImageFileCollection(request.app)))

    if request.current_role == 'admin':
        yield Link(_('Settings'), request.link(
            request.app.org, 'einstellungen'))

    if not request.is_logged_in:
        yield Link(_("Login"), request.link(
            Auth.from_request_path(request), name='login'))

    yield Link('OneGov Cloud', 'http://www.onegovcloud.ch')
    yield Link('Seantis GmbH', 'https://www.seantis.ch')
