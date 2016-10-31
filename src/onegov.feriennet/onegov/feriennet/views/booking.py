from itertools import groupby
from onegov.core.security import Personal
from onegov.activity import AttendeeCollection
from onegov.activity import Booking
from onegov.activity import BookingCollection
from onegov.activity import Occasion
from onegov.core.utils import normalize_for_url
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.layout import BookingCollectionLayout
from sqlalchemy.orm import joinedload


@FeriennetApp.html(
    model=BookingCollection,
    template='bookings.pt',
    permission=Personal)
def view_my_bookings(self, request):
    query = self.query()
    query = query.options(joinedload(Booking.attendee))
    query = query.options(
        joinedload(Booking.occasion).
        joinedload(Occasion.activity))

    bookings = query.all()
    bookings_by_attendee = {
        attendee_id: tuple(bookings)
        for attendee_id, bookings
        in groupby(bookings, key=lambda b: b.attendee_id)
    }

    def first(bookings):
        return bookings and bookings[0] or None

    period = bookings and first(bookings).occasion.period or None

    attendees = AttendeeCollection(request.app.session())\
        .by_username(self.username)\
        .all()
    attendees.sort(key=lambda a: normalize_for_url(a.name))

    return {
        'layout': BookingCollectionLayout(self, request),
        'attendees': attendees,
        'bookings_by_attendee': lambda a: bookings_by_attendee[a.id],
        'period': period,
        'has_bookings': bookings and True or False,
        'title': _("My Bookings")
    }
