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
        screen_count = ticket_count.open or ticket_count.pending

        links = []

        links.append(
            Link(
                _("Open Tickets"),
                classes=('with-count', 'alert', 'open-tickets'),
                url=request.class_link(
                    TicketCollection, {'handler': 'ALL', 'state': 'open'}
                ),
                attributes={'data-count': str(ticket_count.open)}
            )
        )

        links.append(
            Link(
                _("Pending Tickets"),
                classes=('with-count', 'info', 'pending-tickets'),
                url=request.class_link(
                    TicketCollection, {'handler': 'ALL', 'state': 'pending'}
                ),
                attributes={'data-count': str(ticket_count.pending)}
            )
        )

        links.append(
            Link(
                _("Closed Tickets"),
                classes=('with-count', 'secondary', 'closed-tickets'),
                url=request.class_link(
                    TicketCollection, {'handler': 'ALL', 'state': 'closed'}
                ),
                attributes={'data-count': str(ticket_count.closed)}
            )
        )

        if screen_count:
            css = ticket_count.open and 'alert' or 'info'
        else:
            css = 'no-tickets'

        yield LinkGroup(
            screen_count == 1 and _("Ticket") or _("Tickets"),
            classes=('with-count', css),
            links=links,
            attributes={'data-count': str(screen_count)}
        )
