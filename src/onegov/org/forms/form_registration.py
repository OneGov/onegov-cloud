from cached_property import cached_property
from onegov.form import Form, FormDefinition
from onegov.form.fields import MultiCheckboxField
from onegov.org import _
from wtforms.fields import BooleanField, RadioField, TextAreaField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms.validators import NumberRange, InputRequired, ValidationError
from wtforms import validators


class FormRegistrationMessageForm(Form):

    message = TextAreaField(
        label=_("Your message"),
        render_kw={'rows': 12},
        validators=[validators.InputRequired()]
    )

    registration_state = MultiCheckboxField(
        label=_("Send to attendees with status"),
        choices=[
            ('open', _("Open")),
            ('confirmed', _("Confirmed")),
            ('cancelled', _("Cancelled")),
        ],
        default=['confirmed'],
        validators=[validators.InputRequired()]
    )

    def ensure_receivers(self):
        receivers = self.receivers
        if not receivers:
            self.registration_state.errors.append(
                _("No email receivers found for the selection")
            )
            return False

    @property
    def receivers(self):
        return {
            subm.email: subm for subm in self.model.submissions
            if subm.registration_state in self.registration_state.data
        }


class FormRegistrationWindowForm(Form):
    """ Form to edit registration windows. """

    start = DateField(
        label=_("Start"),
        validators=[InputRequired()]
    )

    end = DateField(
        label=_("End"),
        validators=[InputRequired()]
    )

    limit_attendees = RadioField(
        label=_("Limit the number of attendees"),
        fieldset=_("Attendees"),
        choices=[
            ('yes', _("Yes, limit the number of attendees")),
            ('no', _("No, allow an unlimited number of attendees"))
        ],
        default='yes'
    )

    limit = IntegerField(
        label=_("Number of attendees"),
        fieldset=_("Attendees"),
        depends_on=('limit_attendees', 'yes'),
        validators=(NumberRange(min=1, max=None), )
    )

    waitinglist = RadioField(
        label=_("Waitinglist"),
        fieldset=_("Attendees"),
        depends_on=('limit_attendees', 'yes'),
        choices=[
            ('yes', _("Yes, allow for more submissions than available spots")),
            ('no', _("No, ensure that all submissions can be confirmed"))
        ],
        default='yes'
    )

    stop = BooleanField(
        label=_("Do not accept any submissions"),
        fieldset=_("Advanced"),
        default=False
    )

    def process_obj(self, obj):
        super().process_obj(obj)
        self.waitinglist.data = obj.overflow and 'yes' or 'no'
        self.limit_attendees.data = obj.limit and 'yes' or 'no'
        self.limit.data = obj.limit or ''
        self.stop.data = not obj.enabled

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)
        obj.overflow = self.waitinglist.data == 'yes'
        obj.limit = self.limit_attendees.data == 'yes' and self.limit.data or 0
        obj.enabled = not self.stop.data

    @cached_property
    def claimed_spots(self):
        return self.model.claimed_spots

    @cached_property
    def requested_spots(self):
        return self.model.requested_spots

    def ensure_start_before_end(self):
        """ Validate start and end for proper error message.
        def ensure_start_end(self) would also be run in side the validate
        function, but the error is not clear. """

        if not self.start.data or not self.end.data:
            return
        if self.start.data >= self.end.data:
            self.end.errors.append(_("Please use a stop date after the start"))
            return False

    def ensure_no_overlapping_windows(self):
        """ Ensure that this registration window does not overlap with other
        already defined registration windows.

        """
        if not self.start.data or not self.end.data:
            return

        form = getattr(self.model, 'form', self.model)
        for existing in form.registration_windows:
            if existing == self.model:
                continue

            latest_start = max(self.start.data, existing.start)
            earliest_end = min(self.end.data, existing.end)
            delta = (earliest_end - latest_start).days + 1
            if delta > 0:
                # circular
                from onegov.org.layout import DefaultLayout
                layout = DefaultLayout(self.model, self.request)

                msg = _(
                    "The date range overlaps with an existing registration "
                    "window (${range}).",
                    mapping={
                        'range': layout.format_date_range(
                            existing.start, existing.end
                        )
                    }
                )
                self.start.errors.append(msg)
                self.end.errors.append(msg)
                return False

    def validate_limit(self, field):

        # new registration windows do not need to enforce limits
        if isinstance(self.model, FormDefinition):
            return

        # nor do unlimited registration windows
        if not self.limit_attendees.data:
            return

        if self.limit.data < self.claimed_spots:
            raise ValidationError(_(
                "The limit cannot be lower than the already confirmed "
                "number of attendees (${claimed_spots})",
                mapping={
                    'claimed_spots': self.claimed_spots
                }
            ))

        # without a waitinglist we guarantee that all people who sent in
        # an attendance request are getting a spot (unless they are maunally
        # cancelled), so we need to take requested spots into account
        if self.waitinglist.data == 'yes':
            return

        if self.limit.data < (self.requested_spots + self.claimed_spots):
            raise ValidationError(_(
                "The limit cannot be lower than the already confirmed "
                "number attendees (${claimed_spots}) and the number of "
                "pending requests (${pending_requests}). Either enable the "
                "waiting list, process the pending requests or increase the "
                "limit. ",
                mapping={
                    'claimed_spots': self.claimed_spots,
                    'pending_requests': self.requested_spots
                }
            ))
