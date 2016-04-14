import sedate

from datetime import time
from onegov.form import Form
from onegov.town import _
from wtforms.fields import RadioField
from wtforms.fields.html5 import EmailField, IntegerField
from wtforms.validators import Email, InputRequired
from wtforms_components import TimeField


# include all fields used below so we can filter them out
# when we merge this form with the custom form definition
RESERVED_FIELDS = [
    'start', 'end', 'email', 'quota', 'whole_day'
]


class ReservationForm(Form):

    def apply_model(self, reservation):

        self.email.data = reservation.email

        if hasattr(self, 'start'):
            self.start.data = reservation.display_start().time()

        if hasattr(self, 'end'):
            self.end.data = reservation.display_end().time()

        if hasattr(self, 'start') and hasattr(self, 'end'):
            if self.start.data == self.end.data:
                self.start.data = None
                self.end.data = None

        if hasattr(self, 'quota'):
            self.quota.data = reservation.quota

        if hasattr(self, 'whole_day'):
            if self.start.data == self.end.data:
                self.whole_day.data = 'yes'
            else:
                self.whole_day.data = 'no'

    def get_date_range(self):
        if self.allocation.partly_available:
            if self.allocation.whole_day and self.whole_day.data == 'yes':
                start = time(0, 0)
                end = time(23, 59)
            else:
                start = self.start.data
                end = self.end.data

            return sedate.get_date_range(
                sedate.to_timezone(
                    self.allocation.start, self.allocation.timezone
                ),
                start,
                end
            )
        else:
            return self.allocation.start, self.allocation.end

    @classmethod
    def for_allocation(cls, allocation):

        class AdaptedReservationForm(cls):
            # update me when adding new fields!
            reserved_fields = RESERVED_FIELDS

        form_class = AdaptedReservationForm
        form_class.allocation = allocation

        if allocation.partly_available:
            if allocation.whole_day:
                form_class.whole_day = RadioField(
                    label=_("Whole day"),
                    choices=[
                        ('yes', _("Yes")),
                        ('no', _("No"))
                    ],
                    default='yes'
                )

                depends_on = ('whole_day', 'no')
                default_start_time = None
                default_end_time = None
            else:
                depends_on = None
                default_start_time = allocation.display_start().time()
                default_end_time = allocation.display_end().time()

            form_class.start = TimeField(
                label=_("Start"),
                description=_("HH:MM"),
                validators=[InputRequired()],
                default=default_start_time,
                depends_on=depends_on
            )
            form_class.end = TimeField(
                label=_("End"),
                description=_("HH:MM"),
                validators=[InputRequired()],
                default=default_end_time,
                depends_on=depends_on
            )

        form_class.email = EmailField(
            label=_("E-Mail"),
            validators=[InputRequired(), Email()]
        )

        if (allocation.quota or 1) > 1 and allocation.quota_limit != 1:
            form_class.quota = IntegerField(
                label=_("Quota"),
                validators=[InputRequired()],
                default=1
            )

        return form_class
