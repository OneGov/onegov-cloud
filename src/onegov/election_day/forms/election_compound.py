from __future__ import annotations

from datetime import date
from onegov.core.utils import Bunch
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundRelationship
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import PanelField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from re import findall
from sqlalchemy import or_
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import URL
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.request import ElectionDayRequest
    from onegov.file import File
    from wtforms.fields.choices import _Choice


class ElectionCompoundForm(Form):

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

    domain = RadioField(
        label=_('Domain'),
        fieldset=_('Properties'),
        choices=[
            ('canton', _('Cantonal'))
        ],
        default='canton',
        validators=[
            InputRequired()
        ]
    )

    domain_elections = RadioField(
        label=_('Domain of the elections'),
        fieldset=_('Properties'),
        validators=[
            InputRequired()
        ]
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

    region_elections = ChosenSelectMultipleField(
        label=_('Elections'),
        fieldset=_('Properties'),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('domain_elections', 'region'),
    )

    district_elections = ChosenSelectMultipleField(
        label=_('Elections'),
        fieldset=_('Properties'),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('domain_elections', 'district'),
    )

    municipality_elections = ChosenSelectMultipleField(
        label=_('Elections'),
        fieldset=_('Properties'),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('domain_elections', 'municipality'),
    )

    completes_manually = BooleanField(
        label=_('Completes manually'),
        description=_(
            'Enables manual completion of the election compound. '
            'All elections are completed only once the election compound '
            'is completed.'
        ),
        fieldset=_('Completion'),
        render_kw={'force_simple': True}
    )

    manually_completed = BooleanField(
        label=_('Completed'),
        fieldset=_('Completion'),
        depends_on=('completes_manually', 'y'),
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

    related_compounds_historical = ChosenSelectMultipleField(
        label=_('Other legislative periods'),
        fieldset=_('Related elections'),
        choices=[]
    )
    related_compounds_other = ChosenSelectMultipleField(
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
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ],
        fieldset=_('Related link')
    )

    upper_apportionment_pdf = UploadField(
        label=_('Upper apportionment (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ],
        fieldset=_('Related link'),
        depends_on=('pukelsheim', 'y'),
    )

    lower_apportionment_pdf = UploadField(
        label=_('Lower apportionment (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ],
        fieldset=_('Related link'),
        depends_on=('pukelsheim', 'y'),
    )

    pukelsheim = BooleanField(
        label=_('Doppelter Pukelsheim'),
        fieldset=_('View options'),
        description=_('Allows to show the list groups and lists views.'),
        render_kw={'force_simple': True}
    )

    voters_counts = BooleanField(
        label=_('Voters counts'),
        fieldset=_('View options'),
        description=_(
            'Shows voters counts instead of votes in the party strengths '
            'view.'
        ),
    )

    exact_voters_counts = BooleanField(
        label=_('Exact voters counts'),
        fieldset=_('View options'),
        description=_(
            'Shows exact voters counts instead of rounded values.'
        ),
        render_kw={'force_simple': True}
    )

    horizontal_party_strengths = BooleanField(
        label=_('Horizonal party strengths chart'),
        fieldset=_('View options'),
        description=_(
            'Shows a horizontal bar chart instead of a vertical bar chart.'
        ),
        depends_on=('show_party_strengths', 'y'),
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
        render_kw={'force_simple': True}
    )

    show_seat_allocation = BooleanField(
        label=_('Seat allocation'),
        description=_(
            'Shows a tab with the comparison of seat allocation as a bar '
            'chart. Requires party results.'
        ),
        fieldset=_('Views'),
        render_kw={'force_simple': True},
    )

    show_list_groups = BooleanField(
        label=_('List groups'),
        description=_(
            'Shows a tab with list group results. Requires party results with '
            'voters counts. Only if Doppelter Pukelsheim.'
        ),
        fieldset=_('Views'),
        render_kw={'force_simple': True},
        depends_on=('pukelsheim', 'y'),
    )

    show_party_strengths = BooleanField(
        label=_('Party strengths'),
        description=_(
            'Shows a tab with the comparison of party strengths as a bar '
            'chart. Requires party results.'
        ),
        fieldset=_('Views'),
        render_kw={'force_simple': True}
    )

    show_party_panachage = BooleanField(
        label=_('Panachage'),
        description=_(
            'Shows a tab with the panachage. Requires party results.'
        ),
        fieldset=_('Views'),
        render_kw={'force_simple': True}
    )

    color_hint = PanelField(
        label=_('Color suggestions'),
        hide_label=False,
        fieldset=_('Colors'),
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
            query = self.request.session.query(ElectionCompound.id)
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

        self.domain_elections.choices = []
        for domain in ('region', 'district', 'municipality'):
            if domain in principal.domains_election:
                self.domain_elections.choices.append((
                    domain,
                    self.request.translate(principal.domains_election[domain])
                ))

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
            self.title_de.validators.append(InputRequired())
        if default_locale.startswith('rm'):
            self.title_de.validators.append(InputRequired())

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
                ).replace('  ', ' ')
            ) for item in query.filter(Election.domain == 'region')
        ]
        self.district_elections.choices = [
            (
                item.id,
                '{} {} {}'.format(
                    layout.format_date(item.date, 'date'),
                    item.shortcode or '',
                    item.title,
                ).replace('  ', ' ')
            ) for item in query.filter(Election.domain == 'district')
        ]
        self.municipality_elections.choices = [
            (
                item.id,
                '{} {} {}'.format(
                    layout.format_date(item.date, 'date'),
                    item.shortcode or '',
                    item.title,
                ).replace('  ', ' ')
            ) for item in query.filter(Election.domain == 'municipality')
        ]

        query = self.request.session.query(ElectionCompound)
        query = query.order_by(
            ElectionCompound.date.desc(),
            ElectionCompound.shortcode
        )
        choices: list[_Choice] = [
            (
                compound.id,
                '{} {} {}'.format(
                    layout.format_date(compound.date, 'date'),
                    compound.shortcode or '',
                    compound.title,
                ).strip().replace('  ', ' ')
            ) for compound in query
        ]
        self.related_compounds_historical.choices = choices
        self.related_compounds_other.choices = choices

    def update_realtionships(
        self,
        model: ElectionCompound,
        type_: str
    ) -> None:

        # use symetric relationships
        session = self.request.session
        query = session.query(ElectionCompoundRelationship)
        query = query.filter(
            or_(
                ElectionCompoundRelationship.source_id == model.id,
                ElectionCompoundRelationship.target_id == model.id,
            ),
            ElectionCompoundRelationship.type == type_
        )
        for relationship in query:
            session.delete(relationship)

        data = getattr(self, f'related_compounds_{type_}', Bunch(data=[])).data
        for id_ in data:
            if not model.id:
                model.id = model.id_from_title(session)
            session.add(
                ElectionCompoundRelationship(
                    source_id=model.id, target_id=id_, type=type_
                )
            )
            session.add(
                ElectionCompoundRelationship(
                    source_id=id_, target_id=model.id, type=type_
                )
            )

    def update_model(self, model: ElectionCompound) -> None:
        if self.id and self.id.data:
            model.id = self.id.data
        model.external_id = self.external_id.data
        model.domain = self.domain.data
        model.domain_elections = self.domain_elections.data
        assert self.date.data is not None
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
        model.use_historical_party_results = (
            self.use_historical_party_results.data)

        model.elections = []
        query = self.request.session.query(Election)
        if self.domain_elections.data == 'region':
            if self.region_elections.data:
                model.elections = query.filter(
                    Election.id.in_(self.region_elections.data)
                ).all()
        if self.domain_elections.data == 'district':
            if self.district_elections.data:
                model.elections = query.filter(
                    Election.id.in_(self.district_elections.data)
                ).all()
        if self.domain_elections.data == 'municipality':
            if self.municipality_elections.data:
                model.elections = query.filter(
                    Election.id.in_(self.municipality_elections.data)
                ).all()

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

        with self.request.session.no_autoflush:
            self.update_realtionships(model, 'historical')
            self.update_realtionships(model, 'other')

    def apply_model(self, model: ElectionCompound) -> None:
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

        for file_attr in (
            'explanations_pdf',
            'upper_apportionment_pdf',
            'lower_apportionment_pdf'
        ):
            field = getattr(self, file_attr)
            file: File = getattr(model, file_attr)
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
        self.use_historical_party_results.data = (
            model.use_historical_party_results)
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

        self.colors.data = '\n'.join(
            f'{name} {model.colors[name]}' for name in sorted(model.colors)
        )

        self.related_compounds_historical.choices = [
            choice for choice in self.related_compounds_historical.choices
            if choice[0] != model.id
        ]
        self.related_compounds_other.choices = [
            choice for choice in self.related_compounds_other.choices
            if choice[0] != model.id
        ]
        self.related_compounds_historical.data = [
            association.target_id for association in model.related_compounds
            if association.type == 'historical'
        ]
        self.related_compounds_other.data = [
            association.target_id for association in model.related_compounds
            if association.type == 'other'
        ]
