import sedate

from datetime import time
from onegov.form import Form
from onegov.town import _
from wtforms.fields import TextField
from wtforms.fields.html5 import EmailField, IntegerField
from wtforms.validators import Email, InputRequired, Regexp


class ReservationForm(Form):

    def apply_model(self, reservation):

        self.email.data = reservation.email

        if hasattr(self, 'start'):
            self.start.data = '{:%H:%M}'.format(reservation.display_start())

        if hasattr(self, 'end'):
            self.end.data = '{:%H:%M}'.format(reservation.display_end())

        if hasattr(self, 'quota'):
            self.quota.data = reservation.quota

    def get_date_range(self):
        if self.allocation.partly_available:
            return sedate.get_date_range(
                sedate.to_timezone(
                    self.allocation.start, self.allocation.timezone
                ),
                time(*(int(p) for p in self.data['start'].split(':'))),
                time(*(int(p) for p in self.data['end'].split(':')))
            )
        else:
            return self.allocation.start, self.allocation.end

    @classmethod
    def for_allocation(cls, allocation):

        class AdaptedReservationForm(cls):
            pass

        form_class = AdaptedReservationForm
        form_class.allocation = allocation

        if allocation.partly_available:
            time_validator = Regexp(r'[0-9]{2}:[0-9]{2}', message=_(
                "The format of the time is HH:MM (e.g. 14:30)"
            ))

            form_class.start = TextField(
                label=_("Start"),
                description=_("HH:MM"),
                validators=[InputRequired(), time_validator],
                default='{:%H:%M}'.format(allocation.display_start())
            )
            form_class.end = TextField(
                label=_("End"),
                description=_("HH:MM"),
                validators=[InputRequired(), time_validator],
                default='{:%H:%M}'.format(allocation.display_end())
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
