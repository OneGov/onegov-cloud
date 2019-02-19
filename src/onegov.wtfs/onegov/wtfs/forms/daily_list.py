from datetime import date
from onegov.form import Form
from onegov.wtfs import _
from onegov.wtfs.models import DailyListBoxes
from wtforms import RadioField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired


class DailyListSelectionForm(Form):

    date = DateField(
        label=_("Date"),
        validators=[InputRequired()],
        default=date.today
    )

    type = RadioField(
        label=_("Daily list"),
        choices=[
            ('boxes', _("Daily list boxes")),
        ],
        validators=[InputRequired()],
        default='boxes'
    )

    def get_model(self):
        if self.type.data == 'boxes':
            return DailyListBoxes(self.request.session, self.date.data)
