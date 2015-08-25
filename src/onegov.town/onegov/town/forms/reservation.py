from onegov.form import Form
from onegov.town import _
from wtforms.fields import TextField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import InputRequired


class ReservationForm(Form):

    @classmethod
    def for_allocation(cls, allocation, *args, **kwargs):

        class AdaptedReservationForm(cls):
            pass

        form_class = AdaptedReservationForm

        if allocation.partly_available:
            form_class.start = TextField(
                label=_("Start"),
                description=_("HH:MM"),
                validators=[InputRequired()],
                default='{:%H:%M}'.format(allocation.display_start())
            )
            form_class.end = TextField(
                label=_("End"),
                description=_("HH:MM"),
                validators=[InputRequired()],
                default='{:%H:%M}'.format(allocation.display_end())
            )

        if (allocation.quota or 1) > 1 and allocation.quota_limit != 1:
            form_class.quota = IntegerField(
                label=_("Quota"),
                validators=[InputRequired()],
                default=1
            )

        return form_class(*args, **kwargs)
