from datetime import date
from onegov.ballot import Election
from onegov.election_day import _
from onegov.election_day.layouts import DefaultLayout
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import PanelField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from re import findall
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


class ElectionCompoundForm(Form):

    domain = RadioField(
        label=_("Domain"),
        choices=[
            ('canton', _("Cantonal"))
        ],
        default='canton',
        validators=[
            InputRequired()
        ]
    )

    domain_elections = RadioField(
        label=_("Domain of the elections"),
        validators=[
            InputRequired()
        ]
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

    region_elections = ChosenSelectMultipleField(
        label=_("Elections"),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('domain_elections', 'region'),
    )

    district_elections = ChosenSelectMultipleField(
        label=_("Elections"),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('domain_elections', 'district'),
    )

    municipality_elections = ChosenSelectMultipleField(
        label=_("Elections"),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('domain_elections', 'municipality'),
    )

    completes_manually = BooleanField(
        label=_("Completes manually"),
        description=_(
            "Enables manual completion of the election compound. "
            "No indidvidual election results are displayed until the election "
            "compound is manually completed."
        ),
        fieldset=_("Completion"),
        render_kw=dict(force_simple=True)
    )

    manually_completed = BooleanField(
        label=_("Completed"),
        fieldset=_("Completion"),
        depends_on=('completes_manually', 'y'),
        render_kw=dict(force_simple=True)
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
        label=_("Link"),
        fieldset=_("Related link")
    )
    related_link_label_de = StringField(
        label=_("Link label german"),
        fieldset=_("Related link"),
        render_kw={'lang': 'de'}
    )
    related_link_label_fr = StringField(
        label=_("Link label french"),
        fieldset=_("Related link"),
        render_kw={'lang': 'fr'}
    )
    related_link_label_it = StringField(
        label=_("Link label italian"),
        fieldset=_("Related link"),
        render_kw={'lang': 'it'}
    )
    related_link_label_rm = StringField(
        label=_("Link label romansh"),
        fieldset=_("Related link"),
        render_kw={'lang': 'rm'}
    )

    explanations_pdf = UploadField(
        label=_("Explanations (PDF)"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ],
        fieldset=_("Related link")
    )

    upper_apportionment_pdf = UploadField(
        label=_("Upper apportionment (PDF)"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ],
        fieldset=_("Related link"),
        depends_on=('pukelsheim', 'y'),
    )

    lower_apportionment_pdf = UploadField(
        label=_("Lower apportionment (PDF)"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ],
        fieldset=_("Related link"),
        depends_on=('pukelsheim', 'y'),
    )

    pukelsheim = BooleanField(
        label=_("Doppelter Pukelsheim"),
        fieldset=_("View options"),
        description=_("Allows to show the list groups and lists views."),
        render_kw=dict(force_simple=True)
    )

    voters_counts = BooleanField(
        label=_("Voters counts"),
        fieldset=_("View options"),
        description=_(
            "Shows voters counts instead of votes in the party strengths "
            "view."
        ),
    )

    exact_voters_counts = BooleanField(
        label=_("Exact voters counts"),
        fieldset=_("View options"),
        description=_(
            "Shows exact voters counts instead of rounded values."
        ),
        render_kw=dict(force_simple=True)
    )

    horizontal_party_strengths = BooleanField(
        label=_("Horizonal party strengths chart"),
        fieldset=_("View options"),
        description=_(
            "Shows a horizontal bar chart instead of a vertical bar chart."
        ),
        depends_on=('show_party_strengths', 'y'),
        render_kw=dict(force_simple=True)
    )

    show_seat_allocation = BooleanField(
        label=_("Seat allocation"),
        description=_(
            "Shows a tab with the comparison of seat allocation as a bar "
            "chart. Requires party results."
        ),
        fieldset=_("Views"),
        render_kw=dict(force_simple=True),
    )

    show_list_groups = BooleanField(
        label=_("List groups"),
        description=_(
            "Shows a tab with list group results. Requires party results with "
            "voters counts. Only if Doppelter Pukelsheim."
        ),
        fieldset=_("Views"),
        render_kw=dict(force_simple=True),
        depends_on=('pukelsheim', 'y'),
    )

    show_party_strengths = BooleanField(
        label=_("Party strengths"),
        description=_(
            "Shows a tab with the comparison of party strengths as a bar "
            "chart. Requires party results."
        ),
        fieldset=_("Views"),
        render_kw=dict(force_simple=True)
    )

    show_party_panachage = BooleanField(
        label=_("Party panachage"),
        description=_(
            "Shows a tab with the panachage. Requires party results."
        ),
        fieldset=_("Views"),
        render_kw=dict(force_simple=True)
    )

    color_hint = PanelField(
        label=_('Color suggestions'),
        hide_label=False,
        fieldset=_('Colors'),
        text=(
            'AL #a74c97\n'
            'BDP #a9cf00\n'
            'CVP #d28b00\n'
            'EDU #7f6b65\n'
            'EVP #e3c700\n'
            'FDP #0084c7\n'
            'GLP #aeca00\n'
            'GRÜNE #54ba00\n'
            'Piraten #333333\n'
            'SP #c31906\n'
            'SVP #408b3d\n'
        ),
        kind='',
    )

    colors = TextAreaField(
        label=_('Colors'),
        fieldset=_('Colors'),
        render_kw={'rows': 12},
    )

    def parse_colors(self, text):
        if not text:
            return {}
        result = {
            key.strip(): value
            for key, value in findall(r'(.+)\s+(\#[0-9a-fA-F]{6})', text)
        }
        if len(text.strip().splitlines()) != len(result):
            raise ValueError('Could not parse colors')
        return result

    def validate_colors(self, field):
        try:
            self.parse_colors(field.data)
        except Exception:
            raise ValidationError(_('Invalid color definitions'))

    def on_request(self):
        principal = self.request.app.principal

        self.domain_elections.choices = []
        for domain in ('region', 'district', 'municipality'):
            if domain in principal.domains_election:
                self.domain_elections.choices.append((
                    domain,
                    self.request.translate(principal.domains_election[domain])
                ))

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

        layout = DefaultLayout(None, self.request)

        query = self.request.session.query(Election)
        query = query.order_by(Election.date.desc(), Election.shortcode)
        query = query.filter(Election.type == 'proporz')
        self.region_elections.choices = [
            (
                item.id,
                '{} {} {}'.format(
                    layout.format_date(item.date, 'date'),
                    item.shortcode or '',
                    item.title,
                ).replace("  ", " ")
            ) for item in query.filter(Election.domain == 'region')
        ]
        self.district_elections.choices = [
            (
                item.id,
                '{} {} {}'.format(
                    layout.format_date(item.date, 'date'),
                    item.shortcode or '',
                    item.title,
                ).replace("  ", " ")
            ) for item in query.filter(Election.domain == 'district')
        ]
        self.municipality_elections.choices = [
            (
                item.id,
                '{} {} {}'.format(
                    layout.format_date(item.date, 'date'),
                    item.shortcode or '',
                    item.title,
                ).replace("  ", " ")
            ) for item in query.filter(Election.domain == 'municipality')
        ]

    def update_model(self, model):
        model.domain = self.domain.data
        model.domain_elections = self.domain_elections.data
        model.date = self.date.data
        model.shortcode = self.shortcode.data
        model.related_link = self.related_link.data
        model.show_seat_allocation = self.show_seat_allocation.data
        model.show_list_groups = self.show_list_groups.data
        model.show_party_strengths = self.show_party_strengths.data
        model.show_party_panachage = self.show_party_panachage.data
        model.pukelsheim = self.pukelsheim.data
        model.completes_manually = self.completes_manually.data
        model.manually_completed = self.manually_completed.data
        model.voters_counts = self.voters_counts.data
        model.exact_voters_counts = self.exact_voters_counts.data
        model.horizontal_party_strengths = self.horizontal_party_strengths.data

        model.elections = []
        query = self.request.session.query(Election)
        if self.domain_elections.data == 'region':
            if self.region_elections.data:
                model.elections = query.filter(
                    Election.id.in_(self.region_elections.data)
                )
        if self.domain_elections.data == 'district':
            if self.district_elections.data:
                model.elections = query.filter(
                    Election.id.in_(self.district_elections.data)
                )
        if self.domain_elections.data == 'municipality':
            if self.municipality_elections.data:
                model.elections = query.filter(
                    Election.id.in_(self.municipality_elections.data)
                )

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

        link_labels = {}
        if self.related_link_label_de.data:
            link_labels['de_CH'] = self.related_link_label_de.data
        if self.related_link_label_fr.data:
            link_labels['fr_CH'] = self.related_link_label_fr.data
        if self.related_link_label_it.data:
            link_labels['it_CH'] = self.related_link_label_it.data
        if self.related_link_label_rm.data:
            link_labels['rm_CH'] = self.related_link_label_rm.data
        model.related_link_label = link_labels

        for file in (
            'explanations_pdf',
            'upper_apportionment_pdf',
            'lower_apportionment_pdf'
        ):
            field = getattr(self, file)
            action = getattr(field, 'action', '')
            if action == 'delete':
                delattr(model, file)
            if action == 'replace' and field.data:
                setattr(model, file, (field.file, field.filename,))

        model.colors = self.parse_colors(self.colors.data)

    def apply_model(self, model):
        titles = model.title_translations or {}
        self.election_de.data = titles.get('de_CH')
        self.election_fr.data = titles.get('fr_CH')
        self.election_it.data = titles.get('it_CH')
        self.election_rm.data = titles.get('rm_CH')

        link_labels = model.related_link_label or {}
        self.related_link_label_de.data = link_labels.get('de_CH', '')
        self.related_link_label_fr.data = link_labels.get('fr_CH', '')
        self.related_link_label_it.data = link_labels.get('it_CH', '')
        self.related_link_label_rm.data = link_labels.get('rm_CH', '')

        for file in (
            'explanations_pdf',
            'upper_apportionment_pdf',
            'lower_apportionment_pdf'
        ):
            field = getattr(self, file)
            file = getattr(model, file)
            if file:
                field.data = {
                    'filename': file.reference.filename,
                    'size': file.reference.file.content_length,
                    'mimetype': file.reference.content_type
                }

        self.domain.data = model.domain
        self.domain_elections.data = model.domain_elections
        self.date.data = model.date
        self.shortcode.data = model.shortcode
        self.related_link.data = model.related_link
        self.pukelsheim.data = model.pukelsheim
        self.completes_manually.data = model.completes_manually
        self.manually_completed.data = model.manually_completed
        self.voters_counts.data = model.voters_counts
        self.exact_voters_counts.data = model.exact_voters_counts
        self.horizontal_party_strengths.data = model.horizontal_party_strengths
        self.show_seat_allocation.data = model.show_seat_allocation
        self.show_list_groups.data = model.show_list_groups
        self.show_party_strengths.data = model.show_party_strengths
        self.show_party_panachage.data = model.show_party_panachage
        self.region_elections.data = []
        if model.domain_elections == 'region':
            self.region_elections.data = [e.id for e in model.elections]
        self.district_elections.data = []
        if model.domain_elections == 'district':
            self.district_elections.data = [e.id for e in model.elections]
        self.municipality_elections.data = []
        if model.domain_elections == 'municipality':
            self.municipality_elections.data = [e.id for e in model.elections]

        self.colors.data = '\n'.join((
            f'{name} {model.colors[name]}' for name in sorted(model.colors)
        ))
