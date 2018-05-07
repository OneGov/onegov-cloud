from datetime import date
from onegov.ballot import Election
from onegov.election_day import _
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms import RadioField
from wtforms import StringField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import URLField
from wtforms.validators import InputRequired


class ElectionCompoundForm(Form):

    domain = RadioField(
        label=_("Type"),
        choices=[
            ('canton', _("Cantonal"))
        ],
        default='canton',
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

    elections = MultiCheckboxField(
        label=_("Elections"),
        choices=[],
        validators=[
            InputRequired()
        ],
    )

    def validate(self):
        result = super(ElectionCompoundForm, self).validate()

        if self.elections.data:
            query = self.request.session.query(Election.type.distinct())
            query = query.filter(Election.id.in_(self.elections.data))
            if query.count() > 1:
                self.elections.errors.append(
                    _("Select either majorz or proporz elections.")
                )
                result = False

        return result

    def on_request(self):
        self.election_de.validators = []
        self.election_fr.validators = []
        self.election_it.validators = []
        self.election_rm.validators = []

        default_locale = self.request.default_locale
        if default_locale.startswith('de'):
            self.election_de.validators.append(InputRequired())
        if default_locale.startswith('fr'):
            self.election_fr.validators.append(InputRequired())
        if default_locale.startswith('it'):
            self.election_de.validators.append(InputRequired())
        if default_locale.startswith('rm'):
            self.election_de.validators.append(InputRequired())

        query = self.request.session.query(Election)
        query = query.order_by(Election.date, Election.shortcode)
        query = query.filter(Election.domain == 'region')
        self.elections.choices = [
            (item.id, '{} ({})'.format(item.title, item.type))
            for item in query
        ]

    def update_model(self, model):
        model.domain = self.domain.data
        model.date = self.date.data
        model.shortcode = self.shortcode.data
        model.related_link = self.related_link.data

        elections = self.request.session.query(Election)
        elections = elections.filter(Election.id.in_(self.elections.data))
        model.elections = elections

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

        self.domain.data = model.domain
        self.date.data = model.date
        self.shortcode.data = model.shortcode
        self.related_link.data = model.related_link
        self.elections.data = [election.id for election in model.elections]
