from __future__ import annotations
from onegov.activity import BookingCollection
from onegov.activity import BookingPeriodCollection
from onegov.activity import VolunteerCollection
from onegov.core.utils import Bunch
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.layout import DefaultLayout
from onegov.org.custom import get_global_tools as get_base_tools
from onegov.core.elements import LinkGroup, Link
from onegov.org.models import Dashboard, ExportCollection


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest
    from onegov.town6.layout import NavigationEntry


@FeriennetApp.template_variables()
def get_template_variables(request: FeriennetRequest) -> RenderData:
    links = {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request)),
        'volunteer_link': None
    }

    if request.app.show_volunteers(request):
        links['volunteer_link'] = Link(
            text=_('Help us'),
            url=request.class_link(
                VacationActivityCollection, name='volunteer'
            ),
            attrs={'id': ('help-us')}
        )  # type:ignore[assignment]

    return links


def get_global_tools(
    request: FeriennetRequest
) -> Iterator[Link | LinkGroup]:
    yield from get_base_tools(request, invoicing=False)
    yield from get_personal_tools(request)
    yield from get_admin_tools(request)


def get_admin_tools(
    request: FeriennetRequest
) -> Iterator[Link | LinkGroup]:
    if request.is_organiser:
        period = request.app.active_period
        periods = request.app.periods

        links = []

        if request.is_admin:
            links.append(
                Link(
                    text=_('Dashboard'),
                    url=request.class_link(Dashboard),
                    attrs={'class': 'show-dashboard'}
                )
            )

            links.append(
                Link(
                    text=_('Periods'),
                    url=request.class_link(BookingPeriodCollection),
                    attrs={'class': 'manage-periods'}
                )
            )

            if periods:
                links.append(
                    Link(
                        text=_('Matching'),
                        url=request.class_link(MatchCollection),
                        attrs={'class': 'manage-matches'}
                    )
                )

                links.append(
                    Link(
                        text=_('Billing'),
                        url=request.class_link(BillingCollection),
                        attrs={'class': 'manage-billing'}
                    )
                )

        if periods:
            if request.is_admin:
                if request.app.show_volunteers(request):
                    links.append(
                        Link(
                            text=_('Volunteers'),
                            url=request.link(
                                VolunteerCollection(
                                    request.session,
                                    period=(period or periods[0])
                                )
                            ),
                            attrs={'class': 'show-volunteers'}
                        )
                    )

                links.append(
                    Link(
                        text=_('Notifications'),
                        url=request.class_link(
                            NotificationTemplateCollection
                        ),
                        attrs={'class': 'show-notifications'}
                    )
                )

                links.append(
                    Link(
                        text=_('Exports'),
                        url=request.class_link(
                            ExportCollection
                        ),
                        attrs={'class': 'show-exports'}
                    )
                )

        if links:
            title = period and period.active and period.title
            title = title or _('No active period')

            if len(title) > 25:
                title = f'{title[:25]}…'

            yield LinkGroup(
                title=title,
                links=links,
                classes=('feriennet-management', )
            )


def get_personal_tools(
    request: FeriennetRequest
) -> Iterator[Link | LinkGroup]:
    # for logged-in users show the number of open bookings
    if request.is_logged_in:
        session = request.session
        username = request.current_username
        assert username is not None
        assert request.current_user is not None

        period = request.app.active_period
        periods = request.app.periods

        if not period or period.finalizable:
            invoices = request.app.invoice_collection(
                user_id=request.current_user.id)

            unpaid = invoices.unpaid_count(excluded_period_ids={
                p.id for p in periods if not p.finalized})

            if unpaid:
                attributes = {
                    'data-count': str(unpaid),
                    'class': {'with-count', 'alert', 'invoices-count'}
                }
            else:
                attributes = {
                    'data-count': '0',
                    'class': {'with-count', 'secondary', 'invoices-count'}
                }

            yield Link(
                text=_('Invoices'),
                url=request.link(invoices),
                attrs=attributes
            )

        bookings = BookingCollection(session)

        if period:
            states: tuple[str, ...]
            if period.confirmed:
                states = ('open', 'accepted')
            else:
                # exclude cancelled bookings even during the wish-phase
                states = ('open', 'blocked', 'accepted', 'denied')

            count = bookings.booking_count(username, states)

            if count:
                attributes = {
                    'data-count': str(count),
                    'class': {
                        'with-count', period.confirmed and 'success' or 'info'
                    }
                }
            else:
                attributes = {
                    'data-count': '0',
                    'class': {'with-count', 'secondary'}
                }

            yield Link(
                text=period.confirmed and _('Bookings') or _('Wishlist'),
                url=request.link(bookings),
                attrs=attributes
            )
        else:
            yield Link(
                text=_('Wishlist'),
                url=request.link(bookings),
                attrs={
                    'data-count': '0',
                    'class': {'with-count', 'secondary'}
                },
            )


def get_top_navigation(
        request: FeriennetRequest) -> Iterator[NavigationEntry]:
    # inject an activites link in front of all top navigation links
    yield (  # type:ignore[misc]
        Bunch(id=-1, access='public', published=True),
        Link(
            text=_('Activities'),
            url=request.class_link(VacationActivityCollection)
        ),
        ()
    )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation or ()
