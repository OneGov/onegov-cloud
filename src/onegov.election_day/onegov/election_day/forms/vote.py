from datetime import date
from onegov.election_day import _
from onegov.form import Form
from wtforms import RadioField, StringField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired


class VoteForm(Form):
    vote = StringField(
        label=_("Vote"),
        validators=[InputRequired()]
    )

    date = DateField(
        label=_("Date"),
        validators=[InputRequired()],
        default=date.today
    )

    domain = RadioField(_("Type"), choices=[
        ('federation', _("Federal Vote")),
        ('canton', _("Cantonal Vote")),
    ], validators=[InputRequired()])

    def update_model(self, model):
        model.title = self.vote.data
        model.date = self.date.data
        model.domain = self.domain.data

    def apply_model(self, model):
        self.vote.data = model.title
        self.date.data = model.date
        self.domain.data = model.domain
