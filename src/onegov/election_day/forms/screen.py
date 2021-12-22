from lxml.etree import XMLSyntaxError
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.core.widgets import transform_structure
from onegov.election_day import _
from onegov.election_day.models import Screen
from onegov.election_day.models.screen import ScreenType
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import CssField
from onegov.form.fields import PanelField
from onegov.form.validators import UniqueColumnValue
from wtforms import IntegerField
from wtforms import RadioField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import ValidationError
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional


class ScreenForm(Form):

    number = IntegerField(
        label=_('Number'),
        validators=[
            InputRequired(),
            NumberRange(min=1),
            UniqueColumnValue(Screen)
        ]
    )

    group = StringField(
        label=_('Group'),
        description=_(
            'Use the same group for all screens you want to cycle through.'
        ),
    )

    duration = IntegerField(
        label=_('Duration'),
        description=_(
            'Number of seconds this screen is presented if cycling trough '
            'screens. If none is set, 20 seconds are used.'
        ),
        validators=[
            NumberRange(min=1),
            Optional()
        ],
    )

    description = StringField(
        label=_('Description')
    )

    type = RadioField(
        label=_('Type'),
        choices=[
            (
                'simple_vote',
                _('Simple Vote')
            ),
            (
                'complex_vote',
                _('Vote with Counter-Proposal')
            ),
            (
                'majorz_election',
                _('Election based on the simple majority system')
            ),
            (
                'proporz_election',
                _('Election based on proportional representation')
            ),
            (
                'election_compound',
                _('Compound of Elections')
            ),
        ],
        validators=[
            InputRequired()
        ],
        default='simple_vote'
    )

    simple_vote = ChosenSelectField(
        _('Vote'),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('type', 'simple_vote'),
    )

    complex_vote = ChosenSelectField(
        _('Vote'),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('type', 'complex_vote'),
    )

    majorz_election = ChosenSelectField(
        _('Election'),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('type', 'majorz_election'),
    )

    proporz_election = ChosenSelectField(
        _('Election'),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('type', 'proporz_election'),
    )

    election_compound = ChosenSelectField(
        _('Compound of Elections'),
        choices=[],
        validators=[
            InputRequired()
        ],
        depends_on=('type', 'election_compound'),
    )

    tags_simple_vote = PanelField(
        label=_('Available tags'),
        text='',
        kind='',
        depends_on=('type', 'simple_vote'),
    )

    tags_complex_vote = PanelField(
        label=_('Available tags'),
        text='',
        kind='',
        depends_on=('type', 'complex_vote'),
    )

    tags_majorz_election = PanelField(
        label=_('Available tags'),
        text='',
        kind='',
        depends_on=('type', 'majorz_election'),
    )

    tags_proporz_election = PanelField(
        label=_('Available tags'),
        text='',
        kind='',
        depends_on=('type', 'proporz_election'),
    )

    tags_election_compound = PanelField(
        label=_('Available tags'),
        text='',
        kind='',
        depends_on=('type', 'election_compound'),
    )

    structure = TextAreaField(
        label=_('Structure'),
        render_kw={'rows': 32},
        validators=[
            InputRequired()
        ],
    )

    css = CssField(
        label=_('Additional CSS'),
        render_kw={'rows': 10},
    )

    def get_widgets(self, type_):
        registry = self.request.app.config.screen_widget_registry
        return registry.by_categories(ScreenType(type_).categories)

    def validate_structure(self, field):
        widgets = self.get_widgets(self.type.data)

        if field.data:
            try:
                transform_structure(widgets.values(), field.data)
            except XMLSyntaxError as e:
                raise ValidationError(e.msg.split(', line')[0])

    def update_model(self, model):
        model.number = self.number.data
        model.group = self.group.data
        model.duration = self.duration.data
        model.description = self.description.data
        model.type = self.type.data
        model.vote_id = None
        model.election_id = None
        model.election_compound_id = None
        if self.type.data == 'simple_vote':
            model.vote_id = self.simple_vote.data
        elif self.type.data == 'complex_vote':
            model.vote_id = self.complex_vote.data
        elif self.type.data == 'majorz_election':
            model.election_id = self.majorz_election.data
        elif self.type.data == 'proporz_election':
            model.election_id = self.proporz_election.data
        elif self.type.data == 'election_compound':
            model.election_compound_id = self.election_compound.data
        model.structure = self.structure.data
        model.css = self.css.data

    def apply_model(self, model):
        self.number.data = model.number
        self.group.data = model.group
        self.duration.data = model.duration
        self.description.data = model.description
        self.type.data = model.type
        self.simple_vote.data = ''
        self.complex_vote.data = ''
        self.majorz_election.data = ''
        self.proporz_election.data = ''
        self.election_compound.data = ''
        if self.type.data == 'simple_vote':
            self.simple_vote.data = model.vote_id
        elif self.type.data == 'complex_vote':
            self.complex_vote.data = model.vote_id
        elif self.type.data == 'majorz_election':
            self.majorz_election.data = model.election_id
        elif self.type.data == 'proporz_election':
            self.proporz_election.data = model.election_id
        elif self.type.data == 'election_compound':
            self.election_compound.data = model.election_compound_id
        self.structure.data = model.structure
        self.css.data = model.css

    def on_request(self):
        session = self.request.session

        query = session.query(Vote).filter_by(type='simple')
        self.simple_vote.choices = [
            (vote.id, f'{vote.title} [{vote.date}]')
            for vote in query.order_by(Vote.date.desc(), Vote.shortcode)
        ]

        query = session.query(Vote).filter_by(type='complex')
        self.complex_vote.choices = [
            (vote.id, f'{vote.title} [{vote.date}]')
            for vote in query.order_by(Vote.date.desc(), Vote.shortcode)
        ]

        query = session.query(Election).filter_by(type='majorz')
        self.majorz_election.choices = [
            (election.id, f'{election.title} [{election.date}]')
            for election in query.order_by(
                Election.date.desc(), Election.shortcode
            )
        ]

        query = session.query(Election).filter_by(type='proporz')
        self.proporz_election.choices = [
            (election.id, f'{election.title} [{election.date}]')
            for election in query.order_by(
                Election.date.desc(), Election.shortcode
            )
        ]

        query = session.query(ElectionCompound)
        self.election_compound.choices = [
            (compound.id, f'{compound.title} [{compound.date}]')
            for compound in query.order_by(
                ElectionCompound.date.desc(), ElectionCompound.shortcode
            )
        ]

        self.tags_simple_vote.text = '\n'.join(sorted([
            tag.usage for tag in self.get_widgets('simple_vote').values()
        ]))
        self.tags_complex_vote.text = '\n'.join(sorted([
            tag.usage for tag in self.get_widgets('complex_vote').values()
        ]))
        self.tags_majorz_election.text = '\n'.join(sorted([
            tag.usage for tag in self.get_widgets('majorz_election').values()
        ]))
        self.tags_proporz_election.text = '\n'.join(sorted([
            tag.usage for tag in self.get_widgets('proporz_election').values()
        ]))
        self.tags_election_compound.text = '\n'.join(sorted([
            tag.usage for tag in self.get_widgets('election_compound').values()
        ]))
