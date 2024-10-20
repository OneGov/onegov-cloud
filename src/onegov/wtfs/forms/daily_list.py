from datetime import date
from onegov.form import Form
from onegov.wtfs import _
from onegov.wtfs.models import DailyListBoxes
from onegov.wtfs.models import DailyListBoxesAndForms
from wtforms.fields import DateField
from wtforms.fields import RadioField
from wtforms.validators import InputRequired


class DailyListSelectionForm(Form):

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        default=date.today
    )

    type = RadioField(
        label=_('Daily list'),
        choices=[
            ('boxes', _('Boxes')),
            ('boxes_and_forms', _('Boxes and forms')),
        ],
        validators=[InputRequired()],
        default='boxes'
    )

    def get_model(self) -> DailyListBoxes | DailyListBoxesAndForms | None:
        if self.type.data == 'boxes':
            return DailyListBoxes(self.request.session, self.date.data)
        if self.type.data == 'boxes_and_forms':
            return DailyListBoxesAndForms(self.request.session, self.date.data)
        return None
