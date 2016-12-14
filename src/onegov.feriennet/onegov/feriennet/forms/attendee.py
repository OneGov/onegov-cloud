from cached_property import cached_property
from datetime import date
from onegov.activity import Attendee, AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.activity import Occasion
from onegov.feriennet import _
from onegov.form import Form
from onegov.user import UserCollection
from purl import URL
from wtforms.fields import RadioField, StringField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired


class AttendeeForm(Form):

    attendee = RadioField(
        label=_("Attendee"),
        validators=[InputRequired()],
        default='0xdeadbeef')

    name = StringField(
        label=_("Full Name"),
        validators=[InputRequired()],
        depends_on=('attendee', 'other'))

    birth_date = DateField(
        label=_("Birthdate"),
        validators=[InputRequired()],
        depends_on=('attendee', 'other'))

    @property
    def is_new(self):
        return self.attendee.data == 'other'

    @property
    def css_class(self):
        return len(self.attendee.choices) == 1 and 'hide-attendee'

    @cached_property
    def username(self):
        if not self.request.is_admin:
            return self.request.current_username

        return self.request.params.get(
            'username', self.request.current_username)

    @cached_property
    def user(self):
        users = UserCollection(self.request.app.session())
        return users.by_username(self.username)

    @cached_property
    def booking_collection(self):
        return BookingCollection(
            session=self.request.app.session(),
            period_id=self.model.period_id)

    def for_username(self, username):
        url = URL(self.action)
        url = url.query_param('username', username)

        return url.as_string()

    def populate_attendees(self):
        assert self.request.is_logged_in

        attendees = AttendeeCollection(self.request.app.session())
        attendees = attendees.by_username(self.username)
        attendees = attendees.with_entities(Attendee.id, Attendee.name)
        attendees = attendees.order_by(Attendee.name)

        self.attendee.choices = [(a.id.hex, a.name) for a in attendees.all()]
        self.attendee.choices.append(('other', _("Other")))

        # override the default
        if self.attendee.data == '0xdeadbeef':
            self.attendee.data = self.attendee.choices[0][0]

    def on_request(self):
        self.populate_attendees()

    def ensure_no_duplicate_child(self):
        if self.is_new:
            attendees = AttendeeCollection(self.request.app.session())
            query = attendees.by_username(self.username)
            query = query.filter(Attendee.name == self.name.data.strip())

            if query.first():
                self.name.errors.append(
                    _("You already entered a child with this name"))

                return False

    def ensure_no_duplicate_booking(self):
        if not self.is_new:
            bookings = self.booking_collection

            query = bookings.by_occasion(self.model)
            query = query.filter(Booking.attendee_id == self.attendee.data)
            query = query.filter(Booking.state != 'cancelled')

            booking = query.first()

            if booking:
                self.attendee.errors.append(_(
                    "This occasion has already been booked by ${name}",
                    mapping={'name': booking.attendee.name}
                ))

                return False

    def ensure_active_period(self):
        if not self.model.period.active:
            self.attendee.errors.append(_(
                "This occasion is outside the currently active period"
            ))
            return False

    def ensure_not_finalized(self):
        if self.model.period.finalized:
            self.attendee.errors.append(_(
                "This period has already been finalized"
            ))
            return False

    def ensure_within_prebooking_period(self):
        if self.model.period.confirmed:
            return

        start, end = (
            self.model.period.prebooking_start,
            self.model.period.prebooking_end
        )
        today = date.today()

        if not (start <= today and today <= end):
            self.attendee.errors.append(_(
                "Cannot create a booking outside the prebooking period"
            ))
            return False

    def ensure_available_spots(self):
        if self.model.full and not self.model.period.wishlist_phase:
            self.attendee.errors.append(_(
                "This occasion is already fully booked"
            ))
            return False

    def ensure_not_over_limit(self):
        if self.is_new:
            return True

        if self.model.period.confirmed and self.model.period.booking_limit:
            bookings = self.booking_collection

            query = bookings.query().with_entities(Booking.id)
            query = query.filter(Booking.attendee_id == self.attendee.data)
            count = query.count()

            if count >= self.model.period.booking_limit:
                self.attendee.errors.append(_((
                    "The attendee already has already reached the maximum "
                    "number of ${count} bookings"
                ), mapping={
                    'count': self.model.period.booking_limit
                }))

                return False

    def ensure_one_booking_per_activity(self):
        if self.is_new:
            return True

        bookings = self.booking_collection

        query = bookings.query().with_entities(Booking.id)
        query = query.filter(Booking.occasion_id.in_(
            self.request.app.session().query(Occasion.id)
            .filter(Occasion.activity_id == self.model.activity_id)
            .subquery()
        ))
        query = query.filter(Booking.attendee_id == self.attendee.data)
        query = query.filter(Booking.period_id == self.model.period_id)
        query = query.filter(Booking.occasion_id != self.model.id)
        query = query.filter(Booking.state != 'cancelled')

        if query.first():
            self.attendee.errors.append(
                _("The attendee already has a booking for this activity")
            )

            return False

    def ensure_no_conflict(self):
        if not self.is_new and self.model.period.confirmed:
            bookings = self.booking_collection

            query = bookings.query()
            query = query.filter(Booking.attendee_id == self.attendee.data)
            query = query.filter(Booking.state == 'accepted')

            for booking in query:
                if booking.overlaps(self.model):
                    self.attendee.errors.append(_(
                        "This occasion overlaps with another booking"
                    ))
                    return False
