from datetime import date
from onegov.ballot import VoteCollection
from onegov.core import utils
from onegov.election_day import _
from onegov.form import Form
from wtforms import RadioField, StringField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired, ValidationError


class VoteForm(Form):
    vote = StringField(
        label=_("Vote"),
        validators=[InputRequired()]
    )

    shortcode = StringField(
        label=_("Shortcode")
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

    def validate_vote(self, field):
        votes = VoteCollection(self.request.app.session())

        if votes.by_id(utils.normalize_for_url(field.data)):
            raise ValidationError(_("A vote with this title exists already"))

    def update_model(self, model):
        model.title = self.vote.data
        model.date = self.date.data
        model.domain = self.domain.data
        model.shortcode = self.shortcode.data

    def apply_model(self, model):
        self.vote.data = model.title
        self.date.data = model.date
        self.domain.data = model.domain
        self.shortcode.data = model.shortcode
