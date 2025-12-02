from __future__ import annotations

from datetime import date
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.models import Ballot
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Vote
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import PanelField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit, MIME_TYPES_PDF
from onegov.form.validators import WhitelistedMimeType
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import URL
from wtforms.validators import ValidationError


from typing import cast
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.request import ElectionDayRequest


class VoteForm(Form):

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

    external_id_counter_proposal = StringField(
        label=_('External ID of counter proposal'),
        fieldset=_('Identifier'),
        render_kw={'long_description': _('Used for import if set.')},
        depends_on=('type', 'complex'),
    )

    external_id_tie_breaker = StringField(
        label=_('External ID of tie breaker'),
        fieldset=_('Identifier'),
        render_kw={'long_description': _('Used for import if set.')},
        depends_on=('type', 'complex'),
    )

    type = RadioField(
        label=_('Type'),
        fieldset=_('Properties'),
        choices=[
            ('simple', _('Simple Vote')),
            ('complex', _('Vote with Counter-Proposal')),
        ],
        validators=[
            InputRequired()
        ],
        default='simple'
    )

    direct = RadioField(
        label=_('Counter Proposal'),
        fieldset=_('Properties'),
        choices=[
            ('direct', _('Direct (Counter Proposal)')),
            ('indirect', _('Indirect (Counter Proposal)')),
        ],
        validators=[
            InputRequired()
        ],
        default='direct',
        depends_on=('type', 'complex')
    )

    domain = RadioField(
        label=_('Domain'),
        fieldset=_('Properties'),
        validators=[
            InputRequired()
        ]
    )

    municipality = ChosenSelectField(
        label=_('Municipality'),
        fieldset=_('Properties'),
        validators=[
            InputRequired()
        ],
        depends_on=('domain', 'municipality'),
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
        validators=[InputRequired()],
        default=date.today
    )

    shortcode = StringField(
        label=_('Shortcode'),
        fieldset=_('Properties'),
        render_kw={'long_description': _('Used for sorting.')}
    )

    tie_breaker_vocabulary = BooleanField(
        label=_('Display as tie-breaker'),
        fieldset=_('View options'),
        depends_on=('type', 'simple'),
        render_kw={'force_simple': True},
    )

    direct_vocabulary = RadioField(
        label=_('Counter Proposal'),
        fieldset=_('View options'),
        choices=[
            ('direct', _('Direct (Counter Proposal)')),
            ('indirect', _('Indirect (Counter Proposal)')),
        ],
        validators=[
            InputRequired()
        ],
        default='direct',
        depends_on=('tie_breaker_vocabulary', 'y')
    )

    title_de = StringField(
        label=_('German'),
        fieldset=_('Title of the the vote/proposal'),
        render_kw={'lang': 'de'}
    )
    title_fr = StringField(
        label=_('French'),
        fieldset=_('Title of the the vote/proposal'),
        render_kw={'lang': 'fr'}
    )
    title_it = StringField(
        label=_('Italian'),
        fieldset=_('Title of the the vote/proposal'),
        render_kw={'lang': 'it'}
    )
    title_rm = StringField(
        label=_('Romansh'),
        fieldset=_('Title of the the vote/proposal'),
        render_kw={'lang': 'rm'}
    )

    short_title_de = StringField(
        label=_('German'),
        fieldset=_('Short title of the the vote/proposal'),
        render_kw={'lang': 'de'}
    )
    short_title_fr = StringField(
        label=_('French'),
        fieldset=_('Short title of the the vote/proposal'),
        render_kw={'lang': 'fr'}
    )
    short_title_it = StringField(
        label=_('Italian'),
        fieldset=_('Short title of the the vote/proposal'),
        render_kw={'lang': 'it'}
    )
    short_title_rm = StringField(
        label=_('Romansh'),
        fieldset=_('Short title of the the vote/proposal'),
        render_kw={'lang': 'rm'}
    )

    counter_proposal_title_de = StringField(
        label=_('German'),
        fieldset=_('Title of the counter proposal'),
        render_kw={'lang': 'de'},
        depends_on=('type', 'complex')
    )
    counter_proposal_title_fr = StringField(
        label=_('French'),
        fieldset=_('Title of the counter proposal'),
        render_kw={'lang': 'fr'},
        depends_on=('type', 'complex')
    )
    counter_proposal_title_it = StringField(
        label=_('Italian'),
        fieldset=_('Title of the counter proposal'),
        render_kw={'lang': 'it'},
        depends_on=('type', 'complex')
    )
    counter_proposal_title_rm = StringField(
        label=_('Romansh'),
        fieldset=_('Title of the counter proposal'),
        render_kw={'lang': 'rm'},
        depends_on=('type', 'complex')
    )

    tie_breaker_title_de = StringField(
        label=_('German'),
        fieldset=_('Title of the tie breaker'),
        render_kw={'lang': 'de'},
        depends_on=('type', 'complex')
    )
    tie_breaker_title_fr = StringField(
        label=_('French'),
        fieldset=_('Title of the tie breaker'),
        render_kw={'lang': 'fr'},
        depends_on=('type', 'complex'),
    )
    tie_breaker_title_it = StringField(
        label=_('Italian'),
        fieldset=_('Title of the tie breaker'),
        render_kw={'lang': 'it'},
        depends_on=('type', 'complex')
    )
    tie_breaker_title_rm = StringField(
        label=_('Romansh'),
        fieldset=_('Title of the tie breaker'),
        render_kw={'lang': 'rm'},
        depends_on=('type', 'complex')
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

    def validate_id(self, field: StringField) -> None:
        if normalize_for_url(field.data or '') != field.data:
            raise ValidationError(_('Invalid ID'))
        if self.model.id != field.data:
            query = self.request.session.query(Vote.id)
            query = query.filter_by(id=field.data)
            if query.first():
                raise ValidationError(_('ID already exists'))

    def validate_external_id(self, field: StringField) -> None:
        if field.data:
            if (
                not hasattr(self.model, 'external_id')
                or self.model.external_id != field.data
            ):
                for cls in (Vote, Ballot):
                    query = self.request.session.query(cls)
                    query = query.filter_by(external_id=field.data)
                    if query.first():
                        raise ValidationError(_('ID already exists'))

    def validate_external_id_counter_proposal(
        self,
        field: StringField
    ) -> None:

        if field.data:
            if (
                not hasattr(self.model, 'counter_proposal')
                or self.model.counter_proposal.external_id != field.data
            ):
                for cls in (Vote, Ballot):
                    query = self.request.session.query(cls)
                    query = query.filter_by(external_id=field.data)
                    if query.first():
                        raise ValidationError(_('ID already exists'))
                if field.data == self.external_id.data:
                    raise ValidationError(_('ID already exists'))

    def validate_external_id_tie_breaker(self, field: StringField) -> None:
        if field.data:
            if (
                not hasattr(self.model, 'tie_breaker')
                or self.model.tie_breaker.external_id != field.data
            ):
                for cls in (Vote, Ballot):
                    query = self.request.session.query(cls)
                    query = query.filter_by(external_id=field.data)
                    if query.first():
                        raise ValidationError(_('ID already exists'))
                if field.data == self.external_id.data:
                    raise ValidationError(_('ID already exists'))
                if field.data == self.external_id_counter_proposal.data:
                    raise ValidationError(_('ID already exists'))

    def on_request(self) -> None:
        principal = self.request.app.principal

        if principal.id != 'zg':
            self.delete_field('tie_breaker_vocabulary')
            self.delete_field('direct_vocabulary')

        self.domain.choices = list(principal.domains_vote.items())

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

    def update_model(self, model: Vote) -> None:
        if self.id and self.id.data:
            model.id = self.id.data
        model.external_id = self.external_id.data
        if isinstance(model, ComplexVote):
            model.direct = self.direct.data == 'direct'
        elif self.direct_vocabulary is not None:
            model.direct = self.direct_vocabulary.data == 'direct'
        assert self.date.data is not None
        model.date = self.date.data
        model.domain = self.domain.data
        if model.domain == 'municipality':
            model.domain_segment = self.municipality.data
        model.has_expats = self.has_expats.data
        model.shortcode = self.shortcode.data
        model.related_link = self.related_link.data
        if self.tie_breaker_vocabulary is not None:
            model.tie_breaker_vocabulary = self.tie_breaker_vocabulary.data

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

        if model.type == 'complex':
            model = cast('ComplexVote', model)
            model.counter_proposal.external_id = (
                self.external_id_counter_proposal.data)
            model.tie_breaker.external_id = self.external_id_tie_breaker.data

            titles = {}
            if self.counter_proposal_title_de.data:
                titles['de_CH'] = self.counter_proposal_title_de.data
            if self.counter_proposal_title_fr.data:
                titles['fr_CH'] = self.counter_proposal_title_fr.data
            if self.counter_proposal_title_it.data:
                titles['it_CH'] = self.counter_proposal_title_it.data
            if self.counter_proposal_title_rm.data:
                titles['rm_CH'] = self.counter_proposal_title_rm.data
            model.counter_proposal.title_translations = titles

            titles = {}
            if self.tie_breaker_title_de.data:
                titles['de_CH'] = self.tie_breaker_title_de.data
            if self.tie_breaker_title_fr.data:
                titles['fr_CH'] = self.tie_breaker_title_fr.data
            if self.tie_breaker_title_it.data:
                titles['it_CH'] = self.tie_breaker_title_it.data
            if self.tie_breaker_title_rm.data:
                titles['rm_CH'] = self.tie_breaker_title_rm.data
            model.tie_breaker.title_translations = titles

    def apply_model(self, model: Vote) -> None:
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

        if isinstance(model, ComplexVote):
            self.direct.data = 'direct' if model.direct else 'indirect'
        elif self.direct_vocabulary is not None:
            self.direct_vocabulary.data = (
                'direct' if model.direct else 'indirect'
            )
        self.date.data = model.date
        self.domain.data = model.domain
        if model.domain == 'municipality':
            self.municipality.data = model.domain_segment
        self.has_expats.data = model.has_expats
        self.shortcode.data = model.shortcode
        self.related_link.data = model.related_link
        if self.tie_breaker_vocabulary is not None:
            self.tie_breaker_vocabulary.data = model.tie_breaker_vocabulary

        file = model.explanations_pdf
        if file:
            self.explanations_pdf.data = {
                'filename': file.reference.filename,
                'size': file.reference.file.content_length,
                'mimetype': file.reference.content_type
            }

        if model.type == 'complex':
            model = cast('ComplexVote', model)
            self.type.choices = [
                ('complex', _('Vote with Counter-Proposal'))
            ]
            self.type.data = 'complex'

            self.external_id_counter_proposal.data = (
                model.counter_proposal.external_id)
            self.external_id_tie_breaker.data = model.tie_breaker.external_id

            titles = model.counter_proposal.title_translations or {}
            self.counter_proposal_title_de.data = titles.get('de_CH')
            self.counter_proposal_title_fr.data = titles.get('fr_CH')
            self.counter_proposal_title_it.data = titles.get('it_CH')
            self.counter_proposal_title_rm.data = titles.get('rm_CH')

            titles = model.tie_breaker.title_translations or {}
            self.tie_breaker_title_de.data = titles.get('de_CH')
            self.tie_breaker_title_fr.data = titles.get('fr_CH')
            self.tie_breaker_title_it.data = titles.get('it_CH')
            self.tie_breaker_title_rm.data = titles.get('rm_CH')

        else:
            self.type.choices = [('simple', _('Simple Vote'))]
            self.type.data = 'simple'

            for fieldset in self.fieldsets:
                if fieldset.label == 'Title of the counter proposal':
                    fieldset.label = None
                if fieldset.label == 'Title of the tie breaker':
                    fieldset.label = None
