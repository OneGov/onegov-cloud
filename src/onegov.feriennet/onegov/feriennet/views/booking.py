import json

from decimal import Decimal
from itertools import groupby
from onegov.activity import Activity, AttendeeCollection
from onegov.activity import Booking
from onegov.activity import BookingCollection
from onegov.activity import Occasion
from onegov.core.security import Personal
from onegov.core.templates import render_macro
from onegov.core.utils import normalize_for_url
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.layout import BookingCollectionLayout
from onegov.feriennet.views.shared import all_periods, all_users
from onegov.org.elements import ConfirmLink, DeleteLink
from sqlalchemy.orm import contains_eager


DELETABLE_STATES = ('open', 'cancelled', 'denied', 'blocked')


def all_bookings(collection):
    """ Loads all bookings together with the linked occasions, attendees and
    activities. This is somewhat of a heavy query, but it beats having to
    load all these things separately.

    """
    query = collection.query()

    query = query.join(Booking.attendee)
    query = query.join(Booking.occasion)
    query = query.join(Occasion.activity)

    query = query.options(contains_eager(Booking.attendee))
    query = query.options(
        contains_eager(Booking.occasion).
        contains_eager(Occasion.activity))

    query = query.order_by(Booking.attendee_id)
    query = query.order_by(Activity.name)
    query = query.order_by(Occasion.start)

    return query.all()


def group_bookings_by_attendee(bookings):
    """ Takes a list of bookings and groups them by attendee. """

    return {
        attendee: tuple(bookings)
        for attendee, bookings
        in groupby(bookings, key=lambda b: b.attendee)
    }


def total_by_bookings(period, bookings):
    if bookings:
        total = sum(
            b.cost for b in bookings
            if b.state == 'accepted' and b.cost
        )
        total = total or Decimal("0.00")
    else:
        return Decimal("0.00")

    if period.all_inclusive and period.booking_cost:
        total += period.booking_cost

    return total


def attendees_by_username(request, username):
    """ Loads the given attendees linked to the given username, sorted by
    their name.

    """

    a = AttendeeCollection(request.app.session()).by_username(username).all()
    a.sort(key=lambda a: normalize_for_url(a.name))

    return a


def get_booking_title(layout, booking):
    return "{} - {}".format(
        booking.occasion.activity.title,
        layout.format_datetime_range(
            booking.occasion.start,
            booking.occasion.end))


def actions_by_booking(layout, period, booking):
    actions = []

    if not period:
        return actions

    if period.wishlist_phase or booking.state in DELETABLE_STATES:
        actions.append(DeleteLink(
            text=_("Remove"),
            url=layout.csrf_protected_url(layout.request.link(booking)),
            confirm=_('Do you really want to remove "${title}"?', mapping={
                'title': get_booking_title(layout, booking)
            }),
            yes_button_text=_("Remove Booking"),
            classes=('confirm', ),
            target='#booking-{}'.format(booking.id)
        ))
    elif period.booking_phase and booking.state == 'accepted':
        actions.append(ConfirmLink(
            text=_("Cancel Booking"),
            url=layout.csrf_protected_url(
                layout.request.link(booking, 'absagen')
            ),
            confirm=_('Do you really want to cancel "${title}"?', mapping={
                'title': get_booking_title(layout, booking)
            }),
            extra_information=_(
                "This cannot be undone! Note that cancellations make it hard "
                "for us to plan and conduct vacation activities. So please be "
                "sure to cancel only if you absolutely have to! We will also "
                "automatically try to accomodate your other wishes should "
                "this cancellation make that possible. To avoid that, delete "
                "your blocked and rejected bookings first."
            ),
            yes_button_text=_("Cancel Booking"),
            redirect_after=layout.request.class_link(BookingCollection),
            classes=('confirm', )
        ))

    return actions


def show_error_on_attendee(request, attendee, message):
    @request.after
    def show_error(response):
        response.headers.add('X-IC-Trigger', 'show-alert')
        response.headers.add('X-IC-Trigger-Data', json.dumps({
            'type': 'alert',
            'target': '#alert-boxes-for-{}'.format(attendee.id),
            'message': request.translate(message)
        }))


@FeriennetApp.html(
    model=BookingCollection,
    template='bookings.pt',
    permission=Personal)
def view_my_bookings(self, request):
    attendees = attendees_by_username(request, self.username)

    bookings = all_bookings(self)
    bookings_by_attendee = group_bookings_by_attendee(bookings)

    periods = all_periods(request)
    period = next((p for p in periods if p.id == self.period_id), None)

    wishlist_phase = not period or period.wishlist_phase

    if request.is_admin:
        users = all_users(request)
        user = next(u for u in users if u.username == self.username)
    else:
        users, user = None, request.current_user

    if user.username == request.current_username:
        title = wishlist_phase and _("Wishlist") or _("Bookings")
    elif wishlist_phase:
        title = _("Wishlist of ${user}", mapping={
            'user': user.title
        })
    else:
        title = _("Bookings of ${user}", mapping={
            'user': user.title
        })

    def get_total(attendee):
        return total_by_bookings(period, bookings_by_attendee.get(attendee))

    def booking_cost(booking):
        if period.confirmed:
            return booking.cost
        else:
            base_cost = 0 if period.all_inclusive else period.booking_cost
            return (booking.occasion.cost or 0) + (base_cost or 0)

    has_emergency_contact = user.data and user.data.get('emergency')
    show_emergency_info = user.username == request.current_username
    layout = BookingCollectionLayout(self, request, title)

    return {
        'actions_by_booking': lambda b: actions_by_booking(layout, period, b),
        'attendees': attendees,
        'bookings_by_attendee': bookings_by_attendee.get,
        'attendee_has_bookings': lambda a: a in bookings_by_attendee,
        'total_by_attendee': get_total,
        'has_bookings': bookings and True or False,
        'booking_cost': booking_cost,
        'layout': layout,
        'model': self,
        'period': period,
        'periods': periods,
        'user': user,
        'users': users,
        'title': title,
        'has_emergency_contact': has_emergency_contact,
        'show_emergency_info': show_emergency_info
    }


@FeriennetApp.view(
    model=Booking,
    permission=Personal,
    request_method='DELETE')
def delete_booking(self, request):
    request.assert_valid_csrf_token()

    if self.period.confirmed and self.state not in DELETABLE_STATES:
        show_error_on_attendee(request, self.attendee, _(
            "Only open, cancelled, denied or blocked bookings may be deleted"))

        return

    BookingCollection(request.app.session()).delete(self)

    @request.after
    def remove_target(response):
        response.headers.add('X-IC-Remove', 'true')


@FeriennetApp.view(
    model=Booking,
    name='absagen',
    permission=Personal,
    request_method='POST')
def cancel_booking(self, request):
    request.assert_valid_csrf_token()
    BookingCollection(request.app.session()).cancel_booking(
        booking=self,
        score_function=self.period.scoring)

    request.success(_("Your booking was cancelled successfully"))


@FeriennetApp.view(
    model=Booking,
    name='toggle-star',
    permission=Personal,
    request_method='POST')
def toggle_star(self, request):

    if self.period.wishlist_phase:
        if not self.starred:
            if not self.star(max_stars=3):
                show_error_on_attendee(request, self.attendee, _(
                    "Cannot select more than three favorites per child"))
        else:
            self.unstar()
    else:
        show_error_on_attendee(request, self.attendee, _(
            "The period is not in the wishlist-phase"))

    layout = BookingCollectionLayout(self, request, None)
    return render_macro(layout.macros['star'], request, {'booking': self})
