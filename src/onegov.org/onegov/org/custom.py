from onegov.org import _, OrgApp
from onegov.org.elements import Link, LinkGroup
from onegov.org.models import GeneralFileCollection, ImageFileCollection
from onegov.user.auth import Auth, UserCollection


@OrgApp.template_variables()
def get_template_variables(request):
    return {
        'global_tools': tuple(get_global_tools(request))
    }


def get_global_tools(request):
    if request.is_logged_in:
        yield LinkGroup(request.current_username, classes=('user', ), links=(
            Link(
                _("User Profile"), classes=('profile', ), url=request.link(
                    request.app.org, name='benutzerprofil'
                )
            ),
            Link(
                _("Logout"), classes=('logout', ), url=request.link(
                    Auth.from_request_path(request), name='logout'
                )
            ),
        ))
    else:
        yield Link(_("Login"), classes=('login', ), url=request.link(
            Auth.from_request_path(request), name='login'
        ))

        if request.app.settings.org.enable_user_registration:
            yield Link(_("Register"), classes=('register', ), url=request.link(
                Auth.from_request_path(request), name='register'
            ))

    if request.is_manager or request.is_admin:
        links = []

        if request.is_manager:
            links.append(
                Link(_("Files"), classes=('files', ), url=request.class_link(
                    GeneralFileCollection
                ))
            )

            links.append(
                Link(_("Images"), classes=('images', ), url=request.class_link(
                    ImageFileCollection
                ))
            )

        if request.is_admin:
            links.append(
                Link(_("Settings"), classes=('settings', ), url=request.link(
                    request.app.org, 'einstellungen'
                ))
            )

            links.append(
                Link(
                    _("Usermanagement"), classes=('users', ),
                    url=request.class_link(UserCollection)
                )
            )

        yield LinkGroup(_("Management"), classes=('management', ), links=links)
