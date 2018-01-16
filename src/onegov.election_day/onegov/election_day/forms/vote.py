from datetime import date
from onegov.election_day import _
from onegov.form import Form
from wtforms import RadioField
from wtforms import StringField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import URLField
from wtforms.validators import InputRequired


class VoteForm(Form):

    vote_type = RadioField(
        _("Type"),
        choices=[
            ('simple', _("Simple Vote")),
            ('complex', _("Vote with Counter-Proposal")),
        ],
        validators=[
            InputRequired()
        ],
        default='simple'
    )

    domain = RadioField(
        label=_("Type"),
        validators=[
            InputRequired()
        ]
    )

    date = DateField(
        label=_("Date"),
        validators=[InputRequired()],
        default=date.today
    )

    shortcode = StringField(
        label=_("Shortcode")
    )

    vote_de = StringField(
        label=_("German"),
        fieldset=_("Title of the the vote/proposal"),
        render_kw={'lang': 'de'}
    )
    vote_fr = StringField(
        label=_("French"),
        fieldset=_("Title of the the vote/proposal"),
        render_kw={'lang': 'fr'}
    )
    vote_it = StringField(
        label=_("Italian"),
        fieldset=_("Title of the the vote/proposal"),
        render_kw={'lang': 'it'}
    )
    vote_rm = StringField(
        label=_("Romansh"),
        fieldset=_("Title of the the vote/proposal"),
        render_kw={'lang': 'rm'}
    )

    counter_proposal_de = StringField(
        label=_("German"),
        fieldset=_("Title of the counter proposal"),
        render_kw={'lang': 'de'},
        depends_on=('vote_type', 'complex')
    )
    counter_proposal_fr = StringField(
        label=_("French"),
        fieldset=_("Title of the counter proposal"),
        render_kw={'lang': 'fr'},
        depends_on=('vote_type', 'complex')
    )
    counter_proposal_it = StringField(
        label=_("Italian"),
        fieldset=_("Title of the counter proposal"),
        render_kw={'lang': 'it'},
        depends_on=('vote_type', 'complex')
    )
    counter_proposal_rm = StringField(
        label=_("Romansh"),
        fieldset=_("Title of the counter proposal"),
        render_kw={'lang': 'rm'},
        depends_on=('vote_type', 'complex')
    )

    tie_breaker_de = StringField(
        label=_("German"),
        fieldset=_("Title of the tie breaker"),
        render_kw={'lang': 'de'},
        depends_on=('vote_type', 'complex')
    )
    tie_breaker_fr = StringField(
        label=_("French"),
        fieldset=_("Title of the tie breaker"),
        render_kw={'lang': 'fr'},
        depends_on=('vote_type', 'complex'),
    )
    tie_breaker_it = StringField(
        label=_("Italian"),
        fieldset=_("Title of the tie breaker"),
        render_kw={'lang': 'it'},
        depends_on=('vote_type', 'complex')
    )
    tie_breaker_rm = StringField(
        label=_("Romansh"),
        fieldset=_("Title of the tie breaker"),
        render_kw={'lang': 'rm'},
        depends_on=('vote_type', 'complex')
    )

    related_link = URLField(
        label=_("Related link")
    )

    def on_request(self):
        self.vote_de.validators = []
        self.vote_fr.validators = []
        self.vote_it.validators = []
        self.vote_rm.validators = []

        default_locale = self.request.default_locale
        if default_locale.startswith('de'):
            self.vote_de.validators.append(InputRequired())
        if default_locale.startswith('fr'):
            self.vote_fr.validators.append(InputRequired())
        if default_locale.startswith('it'):
            self.vote_de.validators.append(InputRequired())
        if default_locale.startswith('rm'):
            self.vote_de.validators.append(InputRequired())

    def set_domain(self, principal):
        self.domain.choices = [
            (key, text)
            for key, text in principal.available_domains.items()
        ]

    def update_model(self, model):
        model.date = self.date.data
        model.domain = self.domain.data
        model.shortcode = self.shortcode.data
        model.related_link = self.related_link.data

        titles = {}
        if self.vote_de.data:
            titles['de_CH'] = self.vote_de.data
        if self.vote_fr.data:
            titles['fr_CH'] = self.vote_fr.data
        if self.vote_it.data:
            titles['it_CH'] = self.vote_it.data
        if self.vote_rm.data:
            titles['rm_CH'] = self.vote_rm.data
        model.title_translations = titles

        if model.type == 'complex':
            titles = {}
            if self.counter_proposal_de.data:
                titles['de_CH'] = self.counter_proposal_de.data
            if self.counter_proposal_fr.data:
                titles['fr_CH'] = self.counter_proposal_fr.data
            if self.counter_proposal_it.data:
                titles['it_CH'] = self.counter_proposal_it.data
            if self.counter_proposal_rm.data:
                titles['rm_CH'] = self.counter_proposal_rm.data
            model.counter_proposal.title_translations = titles

            titles = {}
            if self.tie_breaker_de.data:
                titles['de_CH'] = self.tie_breaker_de.data
            if self.tie_breaker_fr.data:
                titles['fr_CH'] = self.tie_breaker_fr.data
            if self.tie_breaker_it.data:
                titles['it_CH'] = self.tie_breaker_it.data
            if self.tie_breaker_rm.data:
                titles['rm_CH'] = self.tie_breaker_rm.data
            model.tie_breaker.title_translations = titles

    def apply_model(self, model):
        titles = model.title_translations or {}
        self.vote_de.data = titles.get('de_CH')
        self.vote_fr.data = titles.get('fr_CH')
        self.vote_it.data = titles.get('it_CH')
        self.vote_rm.data = titles.get('rm_CH')

        self.date.data = model.date
        self.domain.data = model.domain
        self.shortcode.data = model.shortcode
        self.related_link.data = model.related_link

        if model.type == 'complex':
            self.vote_type.choices = [
                ('complex', _("Vote with Counter-Proposal"))
            ]
            self.vote_type.data = 'complex'

            titles = model.counter_proposal.title_translations or {}
            self.counter_proposal_de.data = titles.get('de_CH')
            self.counter_proposal_fr.data = titles.get('fr_CH')
            self.counter_proposal_it.data = titles.get('it_CH')
            self.counter_proposal_rm.data = titles.get('rm_CH')

            titles = model.tie_breaker.title_translations or {}
            self.tie_breaker_de.data = titles.get('de_CH')
            self.tie_breaker_fr.data = titles.get('fr_CH')
            self.tie_breaker_it.data = titles.get('it_CH')
            self.tie_breaker_rm.data = titles.get('rm_CH')

        else:
            self.vote_type.choices = [('simple', _("Simple Vote"))]
            self.vote_type.data = 'simple'

            for fieldset in self.fieldsets:
                if fieldset.label == 'Title of the counter proposal':
                    fieldset.label = None
                if fieldset.label == 'Title of the tie breaker':
                    fieldset.label = None
