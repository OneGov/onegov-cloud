from __future__ import annotations

from onegov.chat import MessageCollection, TextModuleCollection
from onegov.core.elements import Link, LinkGroup
from onegov.form.collection import FormCollection, SurveyCollection
from onegov.org import _, OrgApp
from onegov.org.models import (
    CitizenDashboard,
    Dashboard,
    GeneralFileCollection,
    ImageFileCollection,
    Organisation,
)
from onegov.pay import PaymentProviderCollection, PaymentCollection
from onegov.reservation import Reservation, ResourceCollection
from onegov.ticket import TicketCollection, TicketInvoiceCollection
from onegov.ticket.collection import ArchivedTicketCollection
from onegov.user import Auth, UserCollection, UserGroupCollection
from purl import URL
from sqlalchemy import func


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.org.request import OrgRequest


@OrgApp.template_variables()
def get_template_variables(request: OrgRequest) -> dict[str, Any]:
    return {
        'global_tools': tuple(get_global_tools(request))
    }


def logout_path(request: OrgRequest) -> str:
    url = URL(request.link(request.app.org))
    return url.path() or '/'


def get_global_tools(
    request: OrgRequest,
    invoicing: bool = True
) -> Iterator[Link | LinkGroup]:

    citizen_login_enabled = request.app.org.citizen_login_enabled

    # Authentication / Userprofile
    if request.is_logged_in:
        yield LinkGroup(_('Account'), classes=('user', ), links=(
            Link(
                _('User Profile'), request.link(
                    request.app.org, name='userprofile'
                ), attrs={'class': 'profile'}
            ),
            Link(
                _('Logout'), request.link(
                    Auth.from_request(
                        request, to=logout_path(request)), name='logout'
                ), attrs={'class': 'logout'}
            ),
        ))

    else:
        yield Link(
            _('Login'), request.link(
                Auth.from_request_path(request), name='login'
            ), attrs={'class': 'login'}
        )

        if citizen_login_enabled and not request.authenticated_email:
            dashboard = CitizenDashboard(request)
            if dashboard.is_available:
                auth = Auth.from_request(
                    request,
                    request.link(dashboard)
                )
            else:
                auth = Auth.from_request_path(request)
            yield Link(
                _('Citizen Login'), request.link(
                    auth, name='citizen-login'
                ), attrs={
                    'class': 'citizen-login',
                    'title': _('No registration necessary')
                }
            )

        if request.app.enable_user_registration:
            yield Link(
                _('Register'), request.link(
                    Auth.from_request_path(request), name='register'
                ), attrs={'class': 'register'})

    # Management dropdown
    if request.is_manager:
        links = []

        links.append(
            Link(
                _('Dashboard'), request.class_link(Dashboard),
                attrs={'class': 'dashboard'}
            )
        )

        links.append(
            Link(
                _('Timeline'), request.class_link(MessageCollection),
                attrs={'class': 'timeline'}
            )
        )

        links.append(
            Link(
                _('Files'), request.class_link(GeneralFileCollection),
                attrs={'class': 'files'}
            )
        )

        links.append(
            Link(
                _('Images'), request.class_link(ImageFileCollection),
                attrs={'class': 'images'}
            )
        )

        if request.is_admin and request.app.payment_providers_enabled:
            links.append(
                Link(
                    _('Payment Provider'),
                    request.class_link(PaymentProviderCollection),
                    attrs={'class': 'payment-provider'}
                )
            )

        links.append(
            Link(
                _('Payments'),
                request.class_link(PaymentCollection),
                attrs={'class': 'payment'}
            )
        )

        if invoicing:
            links.append(
                Link(
                    _('Invoices'),
                    request.class_link(TicketInvoiceCollection),
                    attrs={'class': 'invoice'}
                )
            )

        links.append(
            Link(
                _('Text modules'), request.class_link(TextModuleCollection),
                attrs={'class': 'text-modules'}
            )
        )

        if request.is_admin:
            links.append(
                Link(
                    _('Settings'), request.link(
                        request.app.org, 'settings'
                    ), attrs={'class': 'settings'}
                )
            )

            links.append(
                Link(
                    _('Users'), request.class_link(
                        UserCollection,
                        variables={'active': '1'}
                    ),
                    attrs={'class': 'user'}
                )
            )

            links.append(
                Link(
                    _('User groups'), request.class_link(UserGroupCollection),
                    attrs={'class': 'users'}
                )
            )

            if request.app.org.ris_enabled:
                links.append(
                    Link(
                        _('RIS Settings'),
                        request.link(request.app.org, 'ris-settings'),
                        attrs={'class': 'ris-settings'}
                    ),
                )

            links.append(
                Link(
                    _('Link Check'),
                    request.class_link(Organisation, name='link-check'),
                    attrs={'class': 'link-check'}
                )
            )

        links.append(
            Link(
                _('Archived Tickets'),
                request.class_link(
                    ArchivedTicketCollection, {'handler': 'ALL'}),
                attrs={'class': 'ticket-archive'}
            )
        )

        links.append(
            Link(
                _('Forms'),
                request.class_link(
                    FormCollection),
                attrs={'class': 'forms'}
            )
        )

        links.append(
            Link(
                _('Surveys'),
                request.class_link(
                    SurveyCollection),
                attrs={'class': 'surveys'}
            )
        )

        yield LinkGroup(_('Management'), classes=('management', ), links=links)

    # Tickets
    if request.is_manager or request.is_supporter:
        assert request.current_user is not None
        ticket_count = request.app.ticket_count
        screen_count = ticket_count.open or ticket_count.pending

        links = []

        links.append(
            Link(
                _('My Tickets'),
                request.class_link(
                    TicketCollection, {
                        'handler': 'ALL',
                        'state': 'unfinished',
                        'owner': request.current_user.id.hex
                    },
                ),
                attrs={
                    'class': ('my-tickets'),
                }
            )
        )

        links.append(
            Link(
                _('Open Tickets'),
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
                _('Pending Tickets'),
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
                _('Closed Tickets'),
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
            screen_count == 1 and _('Ticket') or _('Tickets'),
            classes=('with-count', css),
            links=links,
            attributes={'data-count': str(screen_count)}
        )

    if citizen_login_enabled and (email := request.authenticated_email):
        # This logout link is specific to citizens, if we're logged
        # in as another user, then we don't need this additional
        # logout link
        if not request.is_logged_in:
            yield Link(
                _('Logout'),
                request.link(
                    Auth.from_request(request, to=logout_path(request)),
                    name='citizen-logout'
                ),
                attrs={'class': 'logout'}
            )

            yield Link(
                _('Dashboard'),
                request.class_link(CitizenDashboard),
                attrs={'class': 'dashboard'}
            )

        # NOTE: Only show this if we have at least one reservation
        #       this way we don't need a setting to signal whether
        #       or not this instance even accepts reservations.
        if request.session.query(
            request.session.query(Reservation)
            .filter(Reservation.status == 'approved')
            .filter(func.lower(Reservation.email) == email.lower())
            .exists()
        ).scalar():
            yield Link(
                _('My Reservations'),
                request.class_link(
                    ResourceCollection,
                    name='my-reservations'
                ),
                attrs={
                    'class': ('citizen-reservations'),
                }
            )

        yield Link(
            _('My Requests'),
            request.class_link(
                TicketCollection,
                {
                    'handler': 'ALL',
                    'state': 'all',
                },
                name='my-tickets'
            ),
            attrs={
                'class': ('citizen-tickets'),
            }
        )
