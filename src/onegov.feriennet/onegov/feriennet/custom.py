from itertools import chain
from onegov.activity import BookingCollection
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

    # for logged-in users show the number of unconfirmed bookings
    if request.is_logged_in:
        bookings = BookingCollection(request.app.session())
        count = bookings.count(request.current_username)

        if count:
            attributes = {'data-count': str(count)}
        else:
            attributes = {}

        front.append(Link(
            text=_("My Bookings"),
            url=request.link(bookings),
            classes=('count', 'alert'),
            attributes=attributes
        ))

    layout = DefaultLayout(request.app.org, request)
    links = chain(front, layout.top_navigation)

    return {
        'top_navigation': links
    }
