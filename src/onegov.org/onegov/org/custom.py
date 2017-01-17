from onegov.org import _, OrgApp
from onegov.org.elements import Link, LinkGroup
from onegov.org.models import GeneralFileCollection, ImageFileCollection
from onegov.ticket import TicketCollection
from onegov.user.auth import Auth, UserCollection


@OrgApp.template_variables()
def get_template_variables(request):
    return {
        'global_tools': tuple(get_global_tools(request))
    }


def get_global_tools(request):

    # Authentication / Userprofile
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

    # Management dropdown
    if request.is_manager:
        links = []

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
                    _("Users"), classes=('users', ),
                    url=request.class_link(UserCollection)
                )
            )

        yield LinkGroup(_("Management"), classes=('management', ), links=links)

    # Tickets
    if request.is_manager:
        ticket_count = request.app.ticket_count

        pending_label = ticket_count.pending == 1 \
            and _("Pending ticket") or _("Pending tickets")

        yield Link(
            pending_label, classes=('pending-tickets', ),
            url=request.class_link(
                TicketCollection, {'handler': 'ALL', 'state': 'pending'}
            ),
            attributes={'data-count': str(ticket_count.pending)}
        )

        open_label = ticket_count.open == 1 \
            and _("Open ticket") or _("Open tickets")

        yield Link(
            open_label, classes=('open-tickets', ),
            url=request.class_link(
                TicketCollection, {'handler': 'ALL', 'state': 'open'}
            ),
            attributes={'data-count': str(ticket_count.open)}
        )
