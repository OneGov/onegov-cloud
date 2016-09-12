from datetime import date
from onegov.election_day import _
from onegov.form import Form
from wtforms import IntegerField, RadioField, StringField
from wtforms.fields.html5 import DateField, URLField
from wtforms.validators import NumberRange, InputRequired


class ElectionForm(Form):

    election_de = StringField(
        label=_("Election (German)"),
        validators=[
            InputRequired()
        ]
    )
    election_fr = StringField(
        label=_("Election (French)")
    )
    election_it = StringField(
        label=_("Election (Italian)")
    )
    election_rm = StringField(
        label=_("Election (Romansh)")
    )

    shortcode = StringField(
        label=_("Shortcode")
    )

    date = DateField(
        label=_("Date"),
        validators=[
            InputRequired()
        ],
        default=date.today
    )

    mandates = IntegerField(
        label=_("Mandates"),
        validators=[
            InputRequired(),
            NumberRange(min=1)
        ]
    )

    election_type = RadioField(
        label=_("System"),
        choices=[
            ('proporz', _("Election based on proportional representation")),
            ('majorz', _("Majority system")),
        ],
        validators=[
            InputRequired()
        ]
    )

    domain = RadioField(
        label=_("Type"),
        validators=[
            InputRequired()
        ]
    )

    related_link = URLField(
        label=_("Related link")
    )

    def set_domain(self, principal):
        self.domain.choices = [
            (key, text.capitalize())
            for key, text in principal.available_domains.items()
        ]

    def update_model(self, model):
        model.date = self.date.data
        model.domain = self.domain.data
        model.type = self.election_type.data
        model.shortcode = self.shortcode.data
        model.number_of_mandates = self.mandates.data

        model.title_translations = {}
        model.title_translations['de_CH'] = self.election_de.data

        if self.election_fr.data:
            model.title_translations['fr_CH'] = self.election_fr.data

        if self.election_it.data:
            model.title_translations['it_CH'] = self.election_it.data

        if self.election_rm.data:
            model.title_translations['rm_CH'] = self.election_rm.data

        if not model.meta:
            model.meta = {}
        model.meta['related_link'] = self.related_link.data

    def apply_model(self, model):
        self.election_de.data = model.title_translations['de_CH']
        self.election_fr.data = model.title_translations.get('fr_CH')
        self.election_it.data = model.title_translations.get('it_CH')
        self.election_rm.data = model.title_translations.get('rm_CH')

        self.date.data = model.date
        self.domain.data = model.domain
        self.shortcode.data = model.shortcode
        self.election_type.data = model.type
        self.mandates.data = model.number_of_mandates

        meta_data = model.meta or {}
        self.related_link.data = meta_data.get('related_link', '')
