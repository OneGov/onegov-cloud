from __future__ import annotations

from functools import cached_property
from onegov.activity import Attendee, AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.activity import BookingPeriodInvoiceCollection
from onegov.activity import Occasion
from onegov.core.templates import render_macro
from onegov.feriennet import _
from onegov.feriennet.layout import DefaultLayout
from onegov.feriennet.utils import encode_name, decode_name
from onegov.form import Form
from onegov.user import UserCollection
from purl import URL
from sedate import utcnow
from sqlalchemy import not_
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import HiddenField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.validators import Regexp
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired, NumberRange


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest
    from onegov.user import User


class AttendeeBase(Form):

    request: FeriennetRequest

    if TYPE_CHECKING:
        first_name: StringField
        last_name: StringField

    @property
    def name(self) -> str:
        assert self.first_name.data is not None
        assert self.last_name.data is not None
        return encode_name(self.first_name.data, self.last_name.data).strip()

    @name.setter
    def name(self, value: str) -> None:
        self.first_name.data, self.last_name.data = decode_name(value)

    def populate_obj(self, model: Attendee) -> None:  # type:ignore[override]
        super().populate_obj(model)
        model.name = self.name

        # Update name changes on invoice items of current period
        if self.request.app.active_period is not None:
            invoice_collection = BookingPeriodInvoiceCollection(
                session=self.request.session,
                period_id=self.request.app.active_period.id)

            invoice_items = invoice_collection.query_items()

            for item in invoice_items:
                if item.attendee_id == self.model.id:
                    item.group = self.name

    def process_obj(self, model: Attendee) -> None:  # type:ignore[override]
        super().process_obj(model)
        self.name = model.name

    @cached_property
    def username(self) -> str | None:
        if not self.request.is_admin:
            return self.request.current_username

        username = self.request.params.get(
            'username', self.request.current_username)

        return username if isinstance(username, str) else None

    def ensure_no_duplicate_child(self) -> bool | None:
        attendees = AttendeeCollection(self.request.session)
        username = self.username
        if hasattr(self.model, 'username'):
            if self.username != self.model.username:
                username = self.model.username

        assert username is not None
        query = attendees.by_username(username)
        query = query.filter(Attendee.name == self.name)
        query = query.filter(Attendee.id != self.model.id)

        if self.request.session.query(query.exists()).scalar():
            assert isinstance(self.last_name.errors, list)
            self.last_name.errors.append(
                _('You already entered a child with this name'))

            return False
        return None


class AttendeeForm(AttendeeBase):

    first_name = StringField(
        label=_('First Name'),
        validators=[InputRequired()])

    last_name = StringField(
        label=_('Last Name'),
        validators=[InputRequired()])

    birth_date = DateField(
        label=_('Birthdate'),
        validators=[InputRequired()])

    gender = RadioField(
        label=_('Gender'),
        choices=[
            ('female', _('Girl')),
            ('male', _('Boy')),
        ],
        validators=[InputRequired()]
    )

    notes = TextAreaField(
        label=_('Is there anything the course instructor should know?'),
        description=_('Allergies, Disabilities, Particulars'),
    )

    swisspass = StringField(
        label=_('Swisspass ID'),
        description='XXX-XXX-XXX-X',
        render_kw={
            'data-max-length': 13,
        }
    )

    differing_address = BooleanField(
        label=_('The address of the attendee differs from the users address'),
        description=_("Check this box if the attendee doesn't live with you")
    )

    address = TextAreaField(
        label=_('Address'),
        render_kw={'rows': 4},
        validators=[InputRequired()],
        depends_on=('differing_address', 'y')
    )

    zip_code = StringField(
        label=_('Zip Code'),
        validators=[InputRequired()],
        depends_on=('differing_address', 'y')
    )

    place = StringField(
        label=_('Place'),
        validators=[InputRequired()],
        depends_on=('differing_address', 'y')
    )

    political_municipality = StringField(
        label=_('Political municipality'),
        validators=[InputRequired()],
        depends_on=('differing_address', 'y')
    )

    @property
    def show_political_municipality(self) -> bool | None:
        return self.request.app.org.meta.get('show_political_municipality')

    def toggle_political_municipality(self) -> None:
        if not self.show_political_municipality:
            self.delete_field('political_municipality')

    def toggle_swisspass(self) -> None:
        if not self.request.app.org.meta.get('require_swisspass'):
            self.delete_field('swisspass')

    def on_request(self) -> None:
        self.toggle_political_municipality()
        self.toggle_swisspass()

    def ensure_valid_swisspass_id(self) -> bool:
        if self.swisspass and self.swisspass.data:
            if len(self.swisspass.data) != 13:
                assert isinstance(self.swisspass.errors, list)
                self.swisspass.errors.append(_(
                    'The Swisspass ID must be 13 characters long '
                    '(including dashes).'
                ))
                return False

            if not all(c.isdigit() or c == '-' for c in self.swisspass.data):
                assert isinstance(self.swisspass.errors, list)
                self.swisspass.errors.append(_(
                    'The Swisspass ID must only contain digits and dashes.'
                ))
                return False
        return True


class AttendeeSignupForm(AttendeeBase):

    attendee = RadioField(
        label=_('Attendee'),
        validators=[InputRequired()],
        default='0xdeadbeef')

    first_name = StringField(
        label=_('First Name'),
        validators=[InputRequired()],
        depends_on=('attendee', 'other'))

    last_name = StringField(
        label=_('Last Name'),
        validators=[InputRequired()],
        depends_on=('attendee', 'other'))

    birth_date = DateField(
        label=_('Birthdate'),
        validators=[InputRequired()],
        depends_on=('attendee', 'other'))

    gender = RadioField(
        label=_('Gender'),
        choices=[
            ('female', _('Girl')),
            ('male', _('Boy')),
        ],
        validators=[InputRequired()],
        depends_on=('attendee', 'other')
    )

    notes = TextAreaField(
        label=_('Note'),
        description=_('Allergies, Disabilities, Particulars'),
        depends_on=('attendee', 'other')
    )

    swisspass = StringField(
        label=_('Swisspass ID'),
        description='XXX-XXX-XXX-X',
        depends_on=('attendee', 'other'),
        render_kw={
            'data-max-length': 13,
        }
    )

    differing_address = BooleanField(
        label=_('The address of the attendee differs from the users address'),
        description=_("Check this box if the attendee doesn't live with you"),
        depends_on=('attendee', 'other')
    )

    address = TextAreaField(
        label=_('Address'),
        render_kw={'rows': 4},
        validators=[InputRequired()],
        depends_on=('differing_address', 'y')
    )

    zip_code = StringField(
        label=_('Zip Code'),
        validators=[InputRequired()],
        depends_on=('differing_address', 'y')
    )

    place = StringField(
        label=_('Place'),
        validators=[InputRequired()],
        depends_on=('differing_address', 'y')
    )

    political_municipality = StringField(
        label=_('Political Municipality'),
        validators=[InputRequired()],
        depends_on=('differing_address', 'y')
    )

    ignore_age = BooleanField(
        label=_('Ignore Age Restriction'),
        fieldset=_('Administration'),
        default=False
    )

    accept_tos = BooleanField(
        label=_('Accept TOS'),
        fieldset=_('TOS'),
        default=False,
    )

    group_code = HiddenField(
        label=_('Group Code'),
        fieldset=None,
        default=None
    )

    @property
    def is_new_attendee(self) -> bool:
        return self.attendee.data == 'other'

    @property
    def is_complete_userprofile(self) -> bool:
        return self.request.app.settings.org.is_complete_userprofile(
            self.request, username=None, user=self.user)

    @property
    def show_political_municipality(self) -> bool | None:
        return self.request.app.org.meta.get('show_political_municipality')

    @cached_property
    def user(self) -> User | None:
        if not self.username:
            return None
        users = UserCollection(self.request.session)
        return users.by_username(self.username)

    @cached_property
    def booking_collection(self) -> BookingCollection:
        return BookingCollection(
            session=self.request.session,
            period_id=self.model.period_id)

    def toggle_political_municipality(self) -> None:
        if not self.show_political_municipality:
            self.delete_field('political_municipality')

    def toggle_swisspass(self) -> None:
        if not self.request.app.org.meta.get('require_swisspass'):
            self.delete_field('swisspass')

    def for_username(self, username: str) -> str:
        url = URL(self.action)
        url = url.query_param('username', username)

        return url.as_string()

    def populate_attendees(self) -> None:
        assert self.request.is_logged_in
        assert self.username is not None

        attendees = (
            AttendeeCollection(self.request.session)
            .by_username(self.username)
            .with_entities(Attendee.id, Attendee.name)
            .order_by(Attendee.name)
        )

        self.attendee.choices = [(a.id.hex, a.name) for a in attendees]
        self.attendee.choices.append(('other', _('Add a new attendee')))

        # override the default
        if self.attendee.data == '0xdeadbeef':
            self.attendee.data = self.attendee.choices[0][0]

    def populate_tos(self) -> None:
        assert self.request.current_user is not None

        url = self.request.app.org.meta.get('tos_url', None)
        if not url or self.request.current_user.data.get('tos_accepted', None):
            self.delete_field('accept_tos')
            return

        layout = DefaultLayout(self.model, self.request)

        self.accept_tos.description = render_macro(
            layout.macros['accept_tos'], self.request, {'url': url})

    def on_request(self) -> None:
        self.populate_attendees()
        self.populate_tos()
        self.toggle_political_municipality()
        self.toggle_swisspass()

        if not self.request.is_admin:
            self.delete_field('ignore_age')

    def ensure_tos_accepted(self) -> bool | None:
        if hasattr(self, 'accept_tos') and self.accept_tos is not None:
            if not self.accept_tos.data:
                assert isinstance(self.accept_tos.errors, list)
                self.accept_tos.errors.append(
                    _('The TOS must be accepted to create a booking.'))
                return False
        return None

    def ensure_complete_userprofile(self) -> bool | None:
        if not self.is_complete_userprofile:
            assert isinstance(self.attendee.errors, list)
            assert self.user is not None
            if self.user.username == self.request.current_username:
                self.attendee.errors.append(_(
                    'Your userprofile is not complete. It needs to be '
                    'complete before signing up any attendees.'
                ))
            else:
                self.attendee.errors.append(_(
                    "The user's userprofile is not complete. It needs to be "
                    "complete before signing up any attendees."
                ))

            return False
        return None

    def ensure_no_duplicate_booking(self) -> bool | None:
        if not self.is_new_attendee:
            bookings = self.booking_collection

            query = bookings.by_occasion(self.model)
            query = query.filter(Booking.attendee_id == self.attendee.data)
            query = query.filter(not_(
                Booking.state.in_((
                    'cancelled',
                    'denied',
                    'blocked'
                ))
            ))

            booking = query.first()

            if booking:
                assert isinstance(self.attendee.errors, list)
                self.attendee.errors.append(_(
                    'This occasion has already been booked by ${name}',
                    mapping={'name': booking.attendee.name}
                ))

                return False
        return None

    def ensure_active_period(self) -> bool | None:
        if not self.model.period.active:
            assert isinstance(self.attendee.errors, list)
            self.attendee.errors.append(_(
                'This occasion is outside the currently active period'
            ))
            return False
        return None

    def ensure_not_finalized(self) -> bool | None:
        if not self.model.period.finalized:
            return None

        if self.request.is_admin:
            return None

        if self.model.period.book_finalized:
            return None

        assert isinstance(self.attendee.errors, list)
        self.attendee.errors.append(
            _('This period has already been finalized.'))

        return False

    def ensure_within_prebooking_period(self) -> bool | None:
        if self.model.period.confirmed:
            return None

        if not self.model.period.is_currently_prebooking:
            assert isinstance(self.attendee.errors, list)
            self.attendee.errors.append(_(
                'Cannot create a booking outside the prebooking period'
            ))
            return False
        return None

    def ensure_within_booking_period(self) -> bool | None:
        if not self.model.period.confirmed:
            return None

        if self.request.is_admin or self.model.period.book_finalized:
            return None

        if not self.model.period.is_currently_booking:
            assert isinstance(self.attendee.errors, list)
            self.attendee.errors.append(_(
                'Cannot create a booking outside the booking period'
            ))
            return False
        return None

    def ensure_available_spots(self) -> bool | None:
        if self.model.full and not self.model.period.wishlist_phase:
            assert isinstance(self.attendee.errors, list)
            self.attendee.errors.append(_(
                'This occasion is already fully booked'
            ))
            return False
        return None

    def ensure_correct_activity_state(self) -> bool | None:
        if self.model.activity.state == 'approved':
            assert isinstance(self.attendee.errors, list)
            self.attendee.errors.append(_(
                'This is an unapproved activity'
            ))
            return False
        return None

    def ensure_not_over_limit(self) -> bool | None:
        if self.is_new_attendee:
            return True

        if self.model.period.confirmed:
            if self.model.exempt_from_booking_limit:
                limit = None
            elif self.model.period.booking_limit:
                limit = self.model.period.booking_limit
            else:
                limit, = (
                    self.request.session.query(Attendee.limit)
                    .filter(Attendee.id == self.attendee.data)
                    .one()
                )
        else:
            limit = None

        if limit:
            bookings = self.booking_collection

            query = bookings.query().with_entities(Booking.id).join(Occasion)
            query = query.filter(Booking.attendee_id == self.attendee.data)
            query = query.filter(Booking.state == 'accepted')
            query = query.filter(Occasion.exempt_from_booking_limit == False)
            count = query.count()

            if count >= limit:
                assert isinstance(self.attendee.errors, list)
                self.attendee.errors.append(_((
                    'The attendee already has already reached the maximum '
                    'number of ${count} bookings'
                ), mapping={
                    'count': limit
                }))

                return False
        return None

    def ensure_no_conflict(self) -> bool | None:
        if not self.is_new_attendee and self.model.period.confirmed:
            if self.model.exclude_from_overlap_check:
                return None

            bookings = self.booking_collection

            query = bookings.query()
            query = query.filter(Booking.attendee_id == self.attendee.data)
            query = query.filter(Booking.state == 'accepted')

            for booking in query:
                if booking.overlaps(self.model):
                    assert isinstance(self.attendee.errors, list)
                    self.attendee.errors.append(_(
                        'This occasion overlaps with another booking'
                    ))
                    return False
        return None

    def ensure_correct_age(self) -> bool:
        if self.request.is_admin and self.ignore_age.data is True:
            return True

        if self.is_new_attendee and not self.birth_date.data:
            return True  # will be caught by the required validator

        if self.is_new_attendee:
            birth_date = self.birth_date.data
        else:
            attendee = (
                AttendeeCollection(self.request.session)
                .by_id(self.attendee.data)
            )
            assert attendee is not None
            birth_date = attendee.birth_date

        if self.model.is_too_old(birth_date):
            assert isinstance(self.attendee.errors, list)
            self.attendee.errors.append(_('The attendee is too old'))
            return False

        if self.model.is_too_young(birth_date):
            assert isinstance(self.attendee.errors, list)
            self.attendee.errors.append(_('The attendee is too young'))
            return False
        return True

    def ensure_before_deadline(self) -> bool | None:
        if self.request.is_admin:
            return True

        if self.model.is_past_deadline(utcnow()):
            assert isinstance(self.attendee.errors, list)
            self.attendee.errors.append(_('The deadline has passed.'))
            return False

        return None

    def ensure_valid_swisspass_id(self) -> bool:
        if self.swisspass and self.swisspass.data:
            if len(self.swisspass.data) != 13:
                assert isinstance(self.swisspass.errors, list)
                self.swisspass.errors.append(_(
                    'The Swisspass ID must be 13 characters long '
                    '(including dashes).'
                ))
                return False

            if not all(c.isdigit() or c == '-' for c in self.swisspass.data):
                assert isinstance(self.swisspass.errors, list)
                self.swisspass.errors.append(_(
                    'The Swisspass ID must only contain digits and dashes.'
                ))
                return False
        return True


class AttendeeLimitForm(Form):

    limit = IntegerField(
        label=_('Maximum number of bookings per period'),
        validators=[
            NumberRange(0, 1000)
        ])
