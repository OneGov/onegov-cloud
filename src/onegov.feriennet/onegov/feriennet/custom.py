from itertools import chain
from onegov.activity import BookingCollection, PeriodCollection
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.layout import DefaultLayout
from onegov.org.elements import Link


@FeriennetApp.template_variables()
def get_template_variables(request):

    front = []

    # inject an activites link in front of all top navigation links
    front.append(Link(
        text=_("Activities"),
        url=request.class_link(VacationActivityCollection)
    ))

    # for logged-in users show the number of open bookings
    if request.is_logged_in:
        period = PeriodCollection(request.app.session()).active()

        if period:
            bookings = BookingCollection(request.app.session())

            if period.confirmed:
                count = bookings.booking_count(request.current_username)
            else:
                count = bookings.wishlist_count(request.current_username)

            if count:
                attributes = {'data-count': str(count)}
            else:
                attributes = {}

            front.append(Link(
                text=period.confirmed and _("My Bookings") or _("My Wishlist"),
                url=request.link(bookings),
                classes=('count', period.confirmed and 'success' or 'alert'),
                attributes=attributes
            ))

    layout = DefaultLayout(request.app.org, request)
    links = chain(front, layout.top_navigation)

    return {
        'top_navigation': links
    }
