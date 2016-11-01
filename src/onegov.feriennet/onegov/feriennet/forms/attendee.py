from datetime import date
from onegov.activity import Attendee, AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.feriennet import _
from onegov.form import Form
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

    def populate_attendees(self):
        assert self.request.is_logged_in

        attendees = AttendeeCollection(self.request.app.session())
        attendees = attendees.by_username(self.request.current_username)
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
            query = attendees.by_username(self.request.current_username)
            query = query.filter(Attendee.name == self.name.data.strip())

            if query.first():
                self.name.errors.append(
                    _("You already entered a child with this name"))

                return False

        return True

    def ensure_no_duplicate_booking(self):
        if not self.is_new:
            bookings = BookingCollection(self.request.app.session())
            query = bookings.by_occasion(self.model)
            query = query.filter(Booking.attendee_id == self.attendee.data)

            booking = query.first()

            if booking:
                self.attendee.errors.append(_(
                    "This occasion has already been booked by ${name}",
                    mapping={'name': booking.attendee.name}
                ))

                return False

        return True

    def ensure_active_period(self):
        if not self.model.period.active:
            self.attendee.errors.append(_(
                "This occasion is outside the currently active period"
            ))
            return False

        return True

    def ensure_within_prebooking_period(self):
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

        return True

    def validate(self):
        result = super().validate()

        ensurances = (
            self.ensure_active_period,
            self.ensure_within_prebooking_period,
            self.ensure_no_duplicate_child,
            self.ensure_no_duplicate_booking
        )

        for ensurance in ensurances:
            if not ensurance():
                result = False

        return result
