from __future__ import annotations

from datetime import date
from onegov.core.utils import Bunch
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionRelationship
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import PanelField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit, MIME_TYPES_PDF
from onegov.form.validators import WhitelistedMimeType
from re import findall
from sqlalchemy import or_
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional
from wtforms.validators import URL
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.request import ElectionDayRequest
    from wtforms.fields.choices import _Choice


class ElectionForm(Form):

    request: ElectionDayRequest

    id_hint = PanelField(
        label=_('Identifier'),
        fieldset=_('Identifier'),
        kind='callout',
        text=_(
            'The ID is used in the URL and might be used somewhere. '
            'Changing the ID might break links on external sites!'
        )
    )

    id = StringField(
        label=_('Identifier'),
        fieldset=_('Identifier'),
        validators=[
            InputRequired()
        ],
    )

    external_id = StringField(
        label=_('External ID'),
        fieldset=_('Identifier'),
        render_kw={'long_description': _('Used for import if set.')},
    )

    type = RadioField(
        label=_('System'),
        fieldset=_('Properties'),
        choices=[
            ('majorz', _('Election based on the simple majority system')),
            ('proporz', _('Election based on proportional representation')),
        ],
        validators=[
            InputRequired()
        ],
        default='majorz'
    )

    majority_type = RadioField(
        label=_('Majority Type'),
        fieldset=_('Properties'),
        choices=[
            ('absolute', _('Absolute')),
            ('relative', _('Relative')),
        ],
        default='absolute',
        validators=[
            InputRequired()
        ],
        depends_on=('type', 'majorz'),
    )

    absolute_majority = IntegerField(
        label=_('Absolute majority'),
        fieldset=_('Properties'),
        validators=[
            Optional(),
            NumberRange(min=1)
        ],
        depends_on=('majority_type', 'absolute', 'type', 'majorz'),
    )

    domain = RadioField(
        label=_('Domain'),
        fieldset=_('Properties'),
        validators=[
            InputRequired()
        ]
    )

    region = ChosenSelectField(
        label=_('District'),
        fieldset=_('Properties'),
        validators=[
            InputRequired()
        ],
        depends_on=('domain', 'region'),
    )

    district = ChosenSelectField(
        label=_('District'),
        fieldset=_('Properties'),
        validators=[
            InputRequired()
        ],
        depends_on=('domain', 'district'),
    )

    municipality = ChosenSelectField(
        label=_('Municipality'),
        fieldset=_('Properties'),
        validators=[
            InputRequired()
        ],
        depends_on=('domain', 'municipality'),
    )

    tacit = BooleanField(
        label=_('Tacit election'),
        fieldset=_('Properties'),
        render_kw={'force_simple': True}
    )

    has_expats = BooleanField(
        label=_('Expats are listed separately'),
        fieldset=_('Properties'),
        description=_(
            'Expats are uploaded and listed as a separate row in the results. '
            'Changing this option requires a new upload of the data.'
        ),
        render_kw={'force_simple': True}
    )

    date = DateField(
        label=_('Date'),
        fieldset=_('Properties'),
        validators=[
            InputRequired()
        ],
        default=date.today
    )

    shortcode = StringField(
        label=_('Shortcode'),
        fieldset=_('Properties'),
        render_kw={'long_description': _('Used for sorting.')}
    )

    mandates = IntegerField(
        label=_('Mandates / Seats'),
        fieldset=_('Properties'),
        validators=[
            InputRequired(),
            NumberRange(min=1)
        ]
    )

    voters_counts = BooleanField(
        label=_('Voters counts'),
        fieldset=_('View options'),
        description=_(
            'Shows voters counts instead of votes in the party strengths '
            'view.'
        ),
        depends_on=('type', 'proporz'),
    )

    exact_voters_counts = BooleanField(
        label=_('Exact voters counts'),
        fieldset=_('View options'),
        description=_(
            'Shows exact voters counts instead of rounded values.'
        ),
        depends_on=('type', 'proporz'),
        render_kw={'force_simple': True}
    )

    horizontal_party_strengths = BooleanField(
        label=_('Horizonal party strengths chart'),
        fieldset=_('View options'),
        description=_(
            'Shows a horizontal bar chart instead of a vertical bar chart.'
        ),
        depends_on=('type', 'proporz', 'show_party_strengths', 'y'),
        render_kw={'force_simple': True}
    )

    use_historical_party_results = BooleanField(
        label=_('Use party results from the last legislative period'),
        fieldset=_('View options'),
        description=_(
            'Requires party results. Requires a related election from another '
            'legislative period with party results. Requires that both '
            'elections use the same party IDs.'
        ),
        depends_on=('type', 'proporz'),
        render_kw={'force_simple': True}
    )

    show_party_strengths = BooleanField(
        label=_('Party strengths'),
        description=_(
            'Shows a tab with the comparison of party strengths as a bar '
            'chart. Requires party results.'
        ),
        fieldset=_('Views'),
        depends_on=('type', 'proporz'),
        render_kw={'force_simple': True}
    )

    show_party_panachage = BooleanField(
        label=_('Panachage (parties)'),
        description=_(
            'Shows a tab with the panachage. Requires party results.'
        ),
        fieldset=_('Views'),
        depends_on=('type', 'proporz'),
        render_kw={'force_simple': True}
    )

    title_de = StringField(
        label=_('German'),
        fieldset=_('Title of the election'),
        render_kw={'lang': 'de'}
    )
    title_fr = StringField(
        label=_('French'),
        fieldset=_('Title of the election'),
        render_kw={'lang': 'fr'}
    )
    title_it = StringField(
        label=_('Italian'),
        fieldset=_('Title of the election'),
        render_kw={'lang': 'it'}
    )
    title_rm = StringField(
        label=_('Romansh'),
        fieldset=_('Title of the election'),
        render_kw={'lang': 'rm'}
    )

    short_title_de = StringField(
        label=_('German'),
        fieldset=_('Short title of the election'),
        render_kw={'lang': 'de'}
    )
    short_title_fr = StringField(
        label=_('French'),
        fieldset=_('Short title of the election'),
        render_kw={'lang': 'fr'}
    )
    short_title_it = StringField(
        label=_('Italian'),
        fieldset=_('Short title of the election'),
        render_kw={'lang': 'it'}
    )
    short_title_rm = StringField(
        label=_('Romansh'),
        fieldset=_('Short title of the election'),
        render_kw={'lang': 'rm'}
    )

    related_elections_historical = ChosenSelectMultipleField(
        label=_('Other legislative periods'),
        fieldset=_('Related elections'),
        choices=[]
    )

    related_elections_other = ChosenSelectMultipleField(
        label=_('Rounds of voting or by-elections'),
        fieldset=_('Related elections'),
        choices=[]
    )

    related_link = URLField(
        label=_('Link'),
        fieldset=_('Related link'),
        validators=[URL(), Optional()]
    )

    related_link_label_de = StringField(
        label=_('Link label german'),
        fieldset=_('Related link'),
        render_kw={'lang': 'de'}
    )
    related_link_label_fr = StringField(
        label=_('Link label french'),
        fieldset=_('Related link'),
        render_kw={'lang': 'fr'}
    )
    related_link_label_it = StringField(
        label=_('Link label italian'),
        fieldset=_('Related link'),
        render_kw={'lang': 'it'}
    )
    related_link_label_rm = StringField(
        label=_('Link label romansh'),
        fieldset=_('Related link'),
        render_kw={'lang': 'rm'}
    )
    explanations_pdf = UploadField(
        label=_('Explanations (PDF)'),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024)
        ],
        fieldset=_('Related link')
    )

    color_hint = PanelField(
        label=_('Color suggestions'),
        fieldset=_('Colors'),
        hide_label=False,
        text=(
            'AL #a74c97\n'
            'BDP #a9cf00\n'
            'Die Mitte #d28b00\n'
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

    def parse_colors(self, text: str | None) -> dict[str, str]:
        if not text:
            return {}
        result = {
            key.strip(): value
            for key, value in findall(r'(.+)\s+(\#[0-9a-fA-F]{6})', text)
        }
        if len(text.strip().splitlines()) != len(result):
            raise ValueError('Could not parse colors')
        return result

    def validate_colors(self, field: TextAreaField) -> None:
        try:
            self.parse_colors(field.data)
        except Exception as exception:
            raise ValidationError(
                _('Invalid color definitions')
            ) from exception

    def validate_id(self, field: StringField) -> None:
        if normalize_for_url(field.data or '') != field.data:
            raise ValidationError(_('Invalid ID'))
        if self.model.id != field.data:
            query = self.request.session.query(Election)
            query = query.filter_by(id=field.data)
            if query.first():
                raise ValidationError(_('ID already exists'))

    def validate_external_id(self, field: StringField) -> None:
        if field.data:
            if (
                not hasattr(self.model, 'external_id')
                or self.model.external_id != field.data
            ):
                for cls in (Election, ElectionCompound):
                    query = self.request.session.query(cls)
                    query = query.filter_by(external_id=field.data)
                    if query.first():
                        raise ValidationError(_('ID already exists'))

    def on_request(self) -> None:
        principal = self.request.app.principal

        self.domain.choices = [
            (key, self.request.translate(text))
            for key, text in principal.domains_election.items()
        ]

        self.region.label.text = principal.label('region')
        regions = {
            region
            for year in principal.entities.values()
            for entity in year.values()
            if (region := entity.get('region', None))
        }
        self.region.choices = [(item, item) for item in sorted(regions)]

        self.district.label.text = principal.label('district')
        districts = {
            district
            for year in principal.entities.values()
            for entity in year.values()
            if (district := entity.get('district', None))
        }
        self.district.choices = [(item, item) for item in sorted(districts)]

        municipalities = {
            municipality
            for year in principal.entities.values()
            for entity in year.values()
            if (municipality := entity.get('name', None))
        }
        self.municipality.choices = [
            (item, item) for item in sorted(municipalities)
        ]
        if principal.domain == 'municipality':
            assert principal.name is not None
            self.municipality.choices = [(principal.name, principal.name)]

        self.title_de.validators = []
        self.title_fr.validators = []
        self.title_it.validators = []
        self.title_rm.validators = []
        default_locale = self.request.default_locale or ''
        if default_locale.startswith('de'):
            self.title_de.validators.append(InputRequired())
        if default_locale.startswith('fr'):
            self.title_fr.validators.append(InputRequired())
        if default_locale.startswith('it'):
            self.title_it.validators.append(InputRequired())
        if default_locale.startswith('rm'):
            self.title_rm.validators.append(InputRequired())

        layout = DefaultLayout(None, self.request)

        query = self.request.session.query(Election)
        query = query.order_by(Election.date.desc(), Election.shortcode)
        choices: list[_Choice] = [
            (
                election.id,
                '{} {} {}'.format(
                    layout.format_date(election.date, 'date'),
                    election.shortcode or '',
                    election.title,
                ).strip().replace('  ', ' ')
            ) for election in query
        ]
        self.related_elections_historical.choices = choices
        self.related_elections_other.choices = choices

    def update_realtionships(self, model: Election, type_: str) -> None:
        # use symetric relationships
        session = self.request.session
        query = session.query(ElectionRelationship)
        query = query.filter(
            or_(
                ElectionRelationship.source_id == model.id,
                ElectionRelationship.target_id == model.id,
            ),
            ElectionRelationship.type == type_
        )
        for relationship in query:
            session.delete(relationship)

        data = getattr(self, f'related_elections_{type_}', Bunch(data=[])).data
        for id_ in data:
            if not model.id:
                model.id = model.id_from_title(session)
            session.add(
                ElectionRelationship(
                    source_id=model.id, target_id=id_, type=type_
                )
            )
            session.add(
                ElectionRelationship(
                    source_id=id_, target_id=model.id, type=type_
                )
            )

    def update_model(self, model: Election) -> None:
        principal = self.request.app.principal
        if self.id and self.id.data:
            model.id = self.id.data
        model.external_id = self.external_id.data
        assert self.date.data is not None
        model.date = self.date.data
        model.domain = self.domain.data
        model.domain_supersegment = ''
        if model.domain == 'region':
            model.domain_segment = self.region.data
            model.domain_supersegment = principal.get_superregion(
                self.region.data, self.date.data.year
            )
        if model.domain == 'district':
            model.domain_segment = self.district.data
        if model.domain == 'municipality':
            model.domain_segment = self.municipality.data
        model.type = self.type.data
        model.shortcode = self.shortcode.data
        assert self.mandates.data is not None
        model.number_of_mandates = self.mandates.data
        model.majority_type = self.majority_type.data
        model.absolute_majority = self.absolute_majority.data or None
        model.related_link = self.related_link.data
        model.tacit = self.tacit.data
        model.has_expats = self.has_expats.data
        model.voters_counts = self.voters_counts.data
        model.exact_voters_counts = self.exact_voters_counts.data
        model.horizontal_party_strengths = self.horizontal_party_strengths.data
        model.use_historical_party_results = (
            self.use_historical_party_results.data)
        model.show_party_strengths = self.show_party_strengths.data
        model.show_party_panachage = self.show_party_panachage.data

        titles = {}
        if self.title_de.data:
            titles['de_CH'] = self.title_de.data
        if self.title_fr.data:
            titles['fr_CH'] = self.title_fr.data
        if self.title_it.data:
            titles['it_CH'] = self.title_it.data
        if self.title_rm.data:
            titles['rm_CH'] = self.title_rm.data
        model.title_translations = titles

        titles = {}
        if self.short_title_de.data:
            titles['de_CH'] = self.short_title_de.data
        if self.short_title_fr.data:
            titles['fr_CH'] = self.short_title_fr.data
        if self.short_title_it.data:
            titles['it_CH'] = self.short_title_it.data
        if self.short_title_rm.data:
            titles['rm_CH'] = self.short_title_rm.data
        model.short_title_translations = titles

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

        action = getattr(self.explanations_pdf, 'action', '')
        if action == 'delete':
            del model.explanations_pdf
        if action == 'replace' and self.explanations_pdf.data:
            assert self.explanations_pdf.file is not None
            model.explanations_pdf = (
                self.explanations_pdf.file,
                self.explanations_pdf.filename,
            )

        model.colors = self.parse_colors(self.colors.data)

        with self.request.session.no_autoflush:
            self.update_realtionships(model, 'historical')
            self.update_realtionships(model, 'other')

    def apply_model(self, model: Election) -> None:
        self.id.data = model.id
        self.external_id.data = model.external_id

        titles = model.title_translations or {}
        self.title_de.data = titles.get('de_CH')
        self.title_fr.data = titles.get('fr_CH')
        self.title_it.data = titles.get('it_CH')
        self.title_rm.data = titles.get('rm_CH')

        titles = model.short_title_translations or {}
        self.short_title_de.data = titles.get('de_CH')
        self.short_title_fr.data = titles.get('fr_CH')
        self.short_title_it.data = titles.get('it_CH')
        self.short_title_rm.data = titles.get('rm_CH')

        link_labels = model.related_link_label or {}
        self.related_link_label_de.data = link_labels.get('de_CH', '')
        self.related_link_label_fr.data = link_labels.get('fr_CH', '')
        self.related_link_label_it.data = link_labels.get('it_CH', '')
        self.related_link_label_rm.data = link_labels.get('rm_CH', '')

        file = model.explanations_pdf
        if file:
            self.explanations_pdf.data = {
                'filename': file.reference.filename,
                'size': file.reference.file.content_length,
                'mimetype': file.reference.content_type
            }

        self.date.data = model.date
        self.domain.data = model.domain
        if model.domain == 'region':
            self.region.data = model.domain_segment
        if model.domain == 'district':
            self.district.data = model.domain_segment
        if model.domain == 'municipality':
            self.municipality.data = model.domain_segment
        self.shortcode.data = model.shortcode
        self.type.data = model.type
        self.mandates.data = model.number_of_mandates
        self.majority_type.data = model.majority_type
        self.absolute_majority.data = model.absolute_majority
        self.related_link.data = model.related_link
        self.tacit.data = model.tacit
        self.has_expats.data = model.has_expats
        self.horizontal_party_strengths.data = model.horizontal_party_strengths
        self.use_historical_party_results.data = (
            model.use_historical_party_results)
        self.voters_counts.data = model.voters_counts
        self.exact_voters_counts.data = model.exact_voters_counts
        self.show_party_strengths.data = model.show_party_strengths
        self.show_party_panachage.data = model.show_party_panachage

        self.colors.data = '\n'.join(
            f'{name} {model.colors[name]}' for name in sorted(model.colors)
        )

        if model.type == 'majorz':
            self.type.choices = [
                ('majorz', _('Election based on the simple majority system'))
            ]
            self.type.data = 'majorz'

        else:
            self.type.choices = [
                ('proporz', _('Election based on proportional representation'))
            ]
            self.type.data = 'proporz'

        self.related_elections_historical.choices = [
            choice for choice in self.related_elections_historical.choices
            if choice[0] != model.id
        ]
        self.related_elections_other.choices = [
            choice for choice in self.related_elections_other.choices
            if choice[0] != model.id
        ]
        self.related_elections_historical.data = [
            association.target_id for association in model.related_elections
            if association.type == 'historical'
        ]
        self.related_elections_other.data = [
            association.target_id for association in model.related_elections
            if association.type == 'other'
        ]
