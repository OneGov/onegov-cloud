from onegov.chat import MessageCollection
from onegov.org import _, OrgApp
from onegov.org.models import GeneralFileCollection, ImageFileCollection
from onegov.core.elements import Link, LinkGroup
from onegov.pay import PaymentProviderCollection, PaymentCollection
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
                _("User Profile"), request.link(
                    request.app.org, name='userprofile'
                ), attrs={'class': 'profile'}
            ),
            Link(
                _("Logout"), request.link(
                    Auth.from_request_path(request), name='logout'
                ), attrs={'class': 'logout'}
            ),
        ))
    else:
        yield Link(
            _("Login"), request.link(
                Auth.from_request_path(request), name='login'
            ), attrs={'class': 'login'}
        )

        if request.app.enable_user_registration:
            yield Link(
                _("Register"), request.link(
                    Auth.from_request_path(request), name='register'
                ), attrs={'class': 'register'})

    # Management dropdown
    if request.is_manager:
        links = []

        links.append(
            Link(
                _("Timeline"), request.class_link(MessageCollection),
                attrs={'class': 'timeline'}
            )
        )

        links.append(
            Link(
                _("Files"), request.class_link(GeneralFileCollection),
                attrs={'class': 'files'}
            )
        )

        links.append(
            Link(
                _("Images"), request.class_link(ImageFileCollection),
                attrs={'class': 'images'}
            )
        )

        if request.is_admin and request.app.payment_providers_enabled:
            links.append(
                Link(
                    _("Payment Provider"),
                    request.class_link(PaymentProviderCollection),
                    attrs={'class': 'payment-provider'}
                )
            )

        links.append(
            Link(
                _("Payments"),
                request.class_link(PaymentCollection),
                attrs={'class': 'payment'}
            )
        )

        if request.is_admin:
            links.append(
                Link(
                    _("Settings"), request.link(
                        request.app.org, 'settings'
                    ), attrs={'class': 'settings'}
                )
            )

            links.append(
                Link(
                    _("Users"), request.class_link(UserCollection),
                    attrs={'class': 'users'}
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
                request.class_link(
                    TicketCollection, {'handler': 'ALL', 'state': 'open'}
                ),
                attrs={
                    'class': ('with-count', 'alert', 'open-tickets'),
                    'data-count': str(ticket_count.open)
                }
            )
        )

        links.append(
            Link(
                _("Pending Tickets"),
                request.class_link(
                    TicketCollection, {'handler': 'ALL', 'state': 'pending'}
                ),
                attrs={
                    'class': ('with-count', 'info', 'pending-tickets'),
                    'data-count': str(ticket_count.pending)
                }
            )
        )

        links.append(
            Link(
                _("Closed Tickets"),
                url=request.class_link(
                    TicketCollection, {'handler': 'ALL', 'state': 'closed'}
                ),
                attrs={
                    'class': ('with-count', 'secondary', 'closed-tickets'),
                    'data-count': str(ticket_count.closed),
                }
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
