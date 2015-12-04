import sedate

from onegov.form import Form
from onegov.town import _
from wtforms.fields.html5 import EmailField, IntegerField
from wtforms.validators import Email, InputRequired
from wtforms_components import TimeField


class ReservationForm(Form):

    def apply_model(self, reservation):

        self.email.data = reservation.email

        if hasattr(self, 'start'):
            self.start.data = reservation.display_start().time()

        if hasattr(self, 'end'):
            self.end.data = reservation.display_end().time()

        if hasattr(self, 'quota'):
            self.quota.data = reservation.quota

    def get_date_range(self):
        if self.allocation.partly_available:
            return sedate.get_date_range(
                sedate.to_timezone(
                    self.allocation.start, self.allocation.timezone
                ),
                self.start.data,
                self.end.data
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
            form_class.start = TimeField(
                label=_("Start"),
                description=_("HH:MM"),
                validators=[InputRequired()],
                default=allocation.display_start().time()
            )
            form_class.end = TimeField(
                label=_("End"),
                description=_("HH:MM"),
                validators=[InputRequired()],
                default=allocation.display_end().time()
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
