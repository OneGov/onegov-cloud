from datetime import date
from onegov.election_day import _
from onegov.form import Form
from wtforms import IntegerField
from wtforms import RadioField
from wtforms import StringField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import URLField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional


class ElectionForm(Form):

    election_type = RadioField(
        label=_("System"),
        choices=[
            ('majorz', _("Election based on the simple majority system")),
            ('proporz', _("Election based on proportional representation")),
        ],
        validators=[
            InputRequired()
        ],
        default='majorz'
    )

    domain = RadioField(
        label=_("Type"),
        validators=[
            InputRequired()
        ]
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

    shortcode = StringField(
        label=_("Shortcode")
    )

    election_de = StringField(
        label=_("German"),
        fieldset=_("Title of the election"),
        render_kw={'lang': 'de'}
    )
    election_fr = StringField(
        label=_("French"),
        fieldset=_("Title of the election"),
        render_kw={'lang': 'fr'}
    )
    election_it = StringField(
        label=_("Italian"),
        fieldset=_("Title of the election"),
        render_kw={'lang': 'it'}
    )
    election_rm = StringField(
        label=_("Romansh"),
        fieldset=_("Title of the election"),
        render_kw={'lang': 'rm'}
    )

    related_link = URLField(
        label=_("Related link")
    )

    absolute_majority = IntegerField(
        label=_("Absolute majority"),
        validators=[
            Optional(),
            NumberRange(min=1)
        ],
        depends_on=('election_type', 'majorz'),
    )

    def validate(self):
        result = super(ElectionForm, self).validate()
        if not any((
            self.election_de.data,
            self.election_fr.data,
            self.election_it.data,
            self.election_rm.data
        )):
            message = _("Provide at least one title.")
            self.election_de.errors.append(message)
            self.election_fr.errors.append(message)
            self.election_it.errors.append(message)
            self.election_rm.errors.append(message)
            result = False

        return result

    def set_domain(self, principal):
        self.domain.choices = [
            (key, text)
            for key, text in principal.available_domains.items()
        ]

    def update_model(self, model):
        model.date = self.date.data
        model.domain = self.domain.data
        model.type = self.election_type.data
        model.shortcode = self.shortcode.data
        model.number_of_mandates = self.mandates.data
        model.absolute_majority = self.absolute_majority.data
        model.related_link = self.related_link.data

        titles = {}
        if self.election_de.data:
            titles['de_CH'] = self.election_de.data
        if self.election_fr.data:
            titles['fr_CH'] = self.election_fr.data
        if self.election_it.data:
            titles['it_CH'] = self.election_it.data
        if self.election_rm.data:
            titles['rm_CH'] = self.election_rm.data
        model.title_translations = titles

    def apply_model(self, model):
        titles = model.title_translations or {}
        self.election_de.data = titles.get('de_CH')
        self.election_fr.data = titles.get('fr_CH')
        self.election_it.data = titles.get('it_CH')
        self.election_rm.data = titles.get('rm_CH')

        self.date.data = model.date
        self.domain.data = model.domain
        self.shortcode.data = model.shortcode
        self.election_type.data = model.type
        self.mandates.data = model.number_of_mandates
        self.absolute_majority.data = model.absolute_majority
        self.related_link.data = model.related_link

        if model.type == 'majorz':
            self.election_type.choices = [
                ('majorz', _("Election based on the simple majority system"))
            ]
            self.election_type.data = 'majorz'

        else:
            self.election_type.choices = [
                ('proporz', _("Election based on proportional representation"))
            ]
            self.election_type.data = 'proporz'
