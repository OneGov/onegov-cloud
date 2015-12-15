from datetime import date
from onegov.ballot import VoteCollection
from onegov.core import utils
from onegov.election_day import _
from onegov.form import Form
from wtforms import RadioField, StringField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired, ValidationError


class VoteForm(Form):
    vote_de = StringField(
        label=_("Vote (German)"),
        validators=[InputRequired()]
    )

    vote_fr = StringField(label=_("Vote (French)"))
    vote_it = StringField(label=_("Vote (Italian)"))
    vote_rm = StringField(label=_("Vote (Romansh)"))

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
        model.date = self.date.data
        model.domain = self.domain.data
        model.shortcode = self.shortcode.data

        model.title_translations = {}
        model.title_translations['de_CH'] = self.vote_de.data

        if self.vote_fr.data:
            model.title_translations['fr_CH'] = self.vote_fr.data

        if self.vote_it.data:
            model.title_translations['it_CH'] = self.vote_it.data

        if self.vote_rm.data:
            model.title_translations['rm_CH'] = self.vote_rm.data

    def apply_model(self, model):
        self.vote_de.data = model.title_translations['de_CH']
        self.vote_fr.data = model.title_translations.get('fr_CH')
        self.vote_it.data = model.title_translations.get('it_CH')
        self.vote_rm.data = model.title_translations.get('rm_CH')

        self.date.data = model.date
        self.domain.data = model.domain
        self.shortcode.data = model.shortcode
