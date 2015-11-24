from onegov.form import Form
from onegov.town import _
from wtforms.fields import TextField
from wtforms.fields.html5 import EmailField, IntegerField
from wtforms.validators import Email, InputRequired, Regexp


class ReservationForm(Form):

    @classmethod
    def for_allocation(cls, allocation):

        class AdaptedReservationForm(cls):
            pass

        form_class = AdaptedReservationForm

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

        form_class.e_mail = EmailField(
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
