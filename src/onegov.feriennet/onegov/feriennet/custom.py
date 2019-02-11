from onegov.activity import BookingCollection
from onegov.activity import PeriodCollection
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.layout import DefaultLayout
from onegov.org.custom import get_global_tools as get_base_tools
from onegov.core.elements import Link, LinkGroup
from onegov.org.models import ExportCollection


@FeriennetApp.template_variables()
def get_template_variables(request):
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request))
    }


def get_global_tools(request):
    yield from get_base_tools(request)
    yield from get_personal_tools(request)
    yield from get_admin_tools(request)


def get_admin_tools(request):
    if request.is_organiser:
        period = request.app.active_period
        periods = request.app.periods

        links = []

        if request.is_admin:
            links.append(
                Link(
                    text=_("Periods"),
                    url=request.class_link(PeriodCollection),
                    attrs={'class': 'manage-periods'}
                )
            )

            if periods:
                links.append(
                    Link(
                        text=_("Matching"),
                        url=request.class_link(MatchCollection),
                        attrs={'class': 'manage-matches'}
                    )
                )

                links.append(
                    Link(
                        text=_("Billing"),
                        url=request.class_link(BillingCollection),
                        attrs={'class': 'manage-billing'}
                    )
                )

        if periods:
            if request.is_admin:
                links.append(
                    Link(
                        text=_("Notifications"),
                        url=request.class_link(
                            NotificationTemplateCollection
                        ),
                        attrs={'class': 'show-notifications'}
                    )
                )

                links.append(
                    Link(
                        text=_("Exports"),
                        url=request.class_link(
                            ExportCollection
                        ),
                        attrs={'class': 'show-exports'}
                    )
                )

        if links:
            title = period and period.active and period.title
            title = title or _("No active period")

            yield LinkGroup(
                title=title,
                links=links,
                classes=('feriennet-management', )
            )


def get_personal_tools(request):
    # for logged-in users show the number of open bookings
    if request.is_logged_in:
        session = request.session
        username = request.current_username

        period = request.app.active_period
        periods = request.app.periods

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
            text=_("Invoices"),
            url=request.link(invoices),
            attrs=attributes
        )

        bookings = BookingCollection(session)

        if period:
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
                text=period.confirmed and _("Bookings") or _("Wishlist"),
                url=request.link(bookings),
                attrs=attributes
            )
        else:
            yield Link(
                text=_("Wishlist"),
                url=request.link(bookings),
                attrs={
                    'data-count': '0',
                    'class': {'with-count', 'secondary'}
                },
            )


def get_top_navigation(request):

    # inject an activites link in front of all top navigation links
    yield Link(
        text=_("Activities"),
        url=request.class_link(VacationActivityCollection)
    )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation
