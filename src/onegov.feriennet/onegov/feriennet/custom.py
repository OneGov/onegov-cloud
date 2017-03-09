from onegov.activity import BookingCollection
from onegov.activity import InvoiceItemCollection
from onegov.activity import PeriodCollection
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.layout import DefaultLayout
from onegov.org.custom import get_global_tools as get_base_tools
from onegov.org.elements import Link, LinkGroup


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

        links = []

        if request.is_admin:
            links.append(
                Link(
                    text=_("Periods"),
                    url=request.class_link(PeriodCollection),
                    classes=('manage-periods', )
                )
            )

            if period:
                links.append(
                    Link(
                        text=_("Matching"),
                        url=request.class_link(MatchCollection),
                        classes=('manage-matches', )
                    )
                )

                links.append(
                    Link(
                        text=_("Billing"),
                        url=request.class_link(BillingCollection),
                        classes=('manage-billing', )
                    )
                )

        if period:
            links.append(
                Link(
                    text=_("Attendees"),
                    url=request.class_link(OccasionAttendeeCollection),
                    classes=('show-attendees', )
                )
            )

            if request.is_admin:
                links.append(
                    Link(
                        text=_("Notifications"),
                        url=request.class_link(
                            NotificationTemplateCollection
                        ),
                        classes=('show-notifications', )
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
        session = request.app.session()
        username = request.current_username

        period = request.app.active_period
        periods = request.app.periods

        invoice_items = InvoiceItemCollection(session, username)
        unpaid = invoice_items.count_unpaid_invoices(
            exclude_invoices={p.id.hex for p in periods if not p.finalized}
        )

        if unpaid:
            classes = ('with-count', 'alert', 'invoices-count')
            attributes = {'data-count': str(unpaid)}
        else:
            classes = ('with-count', 'secondary', 'invoices-count')
            attributes = {'data-count': '0'}

        yield Link(
            text=_("Invoices"),
            url=request.link(invoice_items),
            classes=classes,
            attributes=attributes
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
                classes = (
                    'with-count', period.confirmed and 'success' or 'info')
                attributes = {'data-count': str(count)}
            else:
                classes = ('with-count', 'secondary')
                attributes = {'data-count': '0'}

            yield Link(
                text=period.confirmed and _("Bookings") or _("Wishlist"),
                url=request.link(bookings),
                classes=classes,
                attributes=attributes
            )
        else:
            yield Link(
                text=_("Wishlist"),
                url=request.link(bookings),
                classes=('with-count', 'secondary'),
                attributes={'data-count': '0'}
            )


def get_top_navigation(request):

    # inject an activites link in front of all top navigation links
    yield Link(
        text=_("Activities"),
        url=request.class_link(VacationActivityCollection)
    )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation
