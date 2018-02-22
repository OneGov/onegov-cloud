from cached_property import cached_property
from datetime import date
from onegov.activity import Attendee, AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.activity import Occasion
from onegov.feriennet import _
from onegov.feriennet.utils import encode_name, decode_name
from onegov.form import Form
from onegov.user import UserCollection
from purl import URL
from sqlalchemy import not_
from wtforms.fields import BooleanField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms.validators import InputRequired, NumberRange


class AttendeeBase(Form):

    @property
    def name(self):
        return encode_name(self.first_name.data, self.last_name.data).strip()

    @name.setter
    def name(self, value):
        self.first_name.data, self.last_name.data = decode_name(value)

    def populate_obj(self, model):
        super().populate_obj(model)
        model.name = self.name

    def process_obj(self, model):
        super().process_obj(model)
        self.name = model.name

    @cached_property
    def username(self):
        if not self.request.is_admin:
            return self.request.current_username

        return self.request.params.get(
            'username', self.request.current_username)

    def ensure_no_duplicate_child(self):
        attendees = AttendeeCollection(self.request.session)
        query = attendees.by_username(self.username)
        query = query.filter(Attendee.name == self.name)
        query = query.filter(Attendee.id != self.model.id)

        if query.first():
            self.last_name.errors.append(
                _("You already entered a child with this name"))

            return False


class AttendeeForm(AttendeeBase):

    first_name = StringField(
        label=_("First Name"),
        validators=[InputRequired()])

    last_name = StringField(
        label=_("Last Name"),
        validators=[InputRequired()])

    birth_date = DateField(
        label=_("Birthdate"),
        validators=[InputRequired()])

    gender = RadioField(
        label=_("Gender"),
        choices=[
            ('female', _("Girl")),
            ('male', _("Boy")),
        ],
        validators=[InputRequired()]
    )

    notes = TextAreaField(
        label=_("Note"),
        description=_("Allergies, Disabilities, Particulars"),
    )


class AttendeeSignupForm(AttendeeBase):

    attendee = RadioField(
        label=_("Attendee"),
        validators=[InputRequired()],
        default='0xdeadbeef')

    first_name = StringField(
        label=_("First Name"),
        validators=[InputRequired()],
        depends_on=('attendee', 'other'))

    last_name = StringField(
        label=_("Last Name"),
        validators=[InputRequired()],
        depends_on=('attendee', 'other'))

    birth_date = DateField(
        label=_("Birthdate"),
        validators=[InputRequired()],
        depends_on=('attendee', 'other'))

    gender = RadioField(
        label=_("Gender"),
        choices=[
            ('female', _("Girl")),
            ('male', _("Boy")),
        ],
        validators=[InputRequired()],
        depends_on=('attendee', 'other')
    )

    notes = TextAreaField(
        label=_("Note"),
        description=_("Allergies, Disabilities, Particulars"),
        depends_on=('attendee', 'other')
    )

    ignore_age = BooleanField(
        label=_("Ignore Age Restriction"),
        fieldset=_("Administration"),
        default=False
    )

    @property
    def is_new(self):
        return self.attendee.data == 'other'

    @property
    def is_complete_userprofile(self):
        return self.request.app.settings.org.is_complete_userprofile(
            self.request, username=None, user=self.user)

    @cached_property
    def user(self):
        users = UserCollection(self.request.session)
        return users.by_username(self.username)

    @cached_property
    def booking_collection(self):
        return BookingCollection(
            session=self.request.session,
            period_id=self.model.period_id)

    def for_username(self, username):
        url = URL(self.action)
        url = url.query_param('username', username)

        return url.as_string()

    def populate_attendees(self):
        assert self.request.is_logged_in

        attendees = AttendeeCollection(self.request.session)
        attendees = attendees.by_username(self.username)
        attendees = attendees.with_entities(Attendee.id, Attendee.name)
        attendees = attendees.order_by(Attendee.name)

        self.attendee.choices = [(a.id.hex, a.name) for a in attendees.all()]
        self.attendee.choices.append(('other', _("Add a new attendee")))

        # override the default
        if self.attendee.data == '0xdeadbeef':
            self.attendee.data = self.attendee.choices[0][0]

    def on_request(self):
        self.populate_attendees()

        if not self.request.is_admin:
            self.delete_field('ignore_age')

    def ensure_complete_userprofile(self):
        if not self.is_complete_userprofile:
            if self.user.username == self.request.current_username:
                self.attendee.errors.append(_(
                    "Your userprofile is not complete. It needs to be "
                    "complete before signing up any attendees."
                ))
            else:
                self.attendee.errors.append(_(
                    "The user's userprofile is not complete. It needs to be "
                    "complete before signing up any attendees."
                ))

            return False

    def ensure_no_duplicate_booking(self):
        if not self.is_new:
            bookings = self.booking_collection

            query = bookings.by_occasion(self.model)
            query = query.filter(Booking.attendee_id == self.attendee.data)
            query = query.filter(not_(
                Booking.state.in_(('cancelled', 'denied'))
            ))

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

        if not self.model.period.is_currently_prebooking:
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

    def ensure_correct_activity_state(self):
        if not self.model.activity.state != 'approved':
            self.attendee.errors.append(_(
                "This is an unapproved activity"
            ))
            return False

    def ensure_not_over_limit(self):
        if self.is_new:
            return True

        if self.model.period.confirmed:
            if self.model.period.booking_limit:
                limit = self.model.period.booking_limit
            else:
                limit = self.request.session.query(Attendee.limit)\
                    .filter(Attendee.id == self.attendee.data)\
                    .one()\
                    .limit
        else:
            limit = None

        if limit:
            bookings = self.booking_collection

            query = bookings.query().with_entities(Booking.id)
            query = query.filter(Booking.attendee_id == self.attendee.data)
            query = query.filter(Booking.state == 'accepted')
            count = query.count()

            if count >= limit:
                self.attendee.errors.append(_((
                    "The attendee already has already reached the maximum "
                    "number of ${count} bookings"
                ), mapping={
                    'count': limit
                }))

                return False

    def ensure_one_booking_per_activity(self):
        if self.is_new:
            return True

        bookings = self.booking_collection

        query = bookings.query().with_entities(Booking.id)
        query = query.filter(Booking.occasion_id.in_(
            self.request.session.query(Occasion.id)
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
            if self.model.exclude_from_overlap_check:
                return

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

    def ensure_correct_age(self):
        if self.request.is_admin and self.ignore_age.data is True:
            return True

        if self.is_new and not self.birth_date.data:
            return True  # will be caught by the required validator

        if self.is_new:
            birth_date = self.birth_date.data
        else:
            attendees = AttendeeCollection(self.request.session)
            birth_date = attendees.by_id(self.attendee.data).birth_date

        if self.model.is_too_old(birth_date):
            self.attendee.errors.append(_("The attendee is too old"))
            return False

        if self.model.is_too_young(birth_date):
            self.attendee.errors.append(_("The attendee is too young"))
            return False

    def ensure_before_deadline(self):
        if self.request.is_admin:
            return True

        if self.model.is_past_deadline(date.today()):
            self.attendee.errors.append(_("The deadline has passed"))
            return False


class AttendeeLimitForm(Form):

    limit = IntegerField(
        label=_("Maximum number of bookings per period"),
        validators=[
            NumberRange(0, 1000)
        ])
