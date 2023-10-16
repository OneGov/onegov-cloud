from onegov.election_day import _
from onegov.form.fields import TypeAheadField
from onegov.form.fields import UploadField
from onegov.form.fields import ChosenSelectField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import PersonFunctionSuggestion
from onegov.landsgemeinde.models import PersonNameSuggestion
from onegov.landsgemeinde.models import PersonPlaceSuggestion
from onegov.landsgemeinde.models import PersonPoliticalAffiliationSuggestion
from onegov.landsgemeinde.models import Votum
from onegov.landsgemeinde.models.votum import STATES
from onegov.org.forms.fields import HtmlField
from onegov.people.collections.people import PersonCollection
from sqlalchemy import desc
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import ValidationError


class VotumForm(NamedFileForm):

    number = IntegerField(
        label=_('Number'),
        fieldset=_('General')
    )

    state = RadioField(
        _('State'),
        fieldset=_('General'),
        choices=list(STATES.items()),
        validators=[
            InputRequired()
        ],
        default=list(STATES.keys())[0]
    )

    body_font_family_ui = ChosenSelectField(
        fieldset=_('Person'),
        label=_('Person from person directory'),
        description=_('Choosing a person will overwrite the fields below'),
        choices=[]
    )

    person_name = TypeAheadField(
        label=_('Name'),
        fieldset=_('Person'),
        url=lambda meta: (
            meta.request.class_link(PersonNameSuggestion) + '?term=%QUERY'
        )
    )

    person_function = TypeAheadField(
        label=_('Function'),
        fieldset=_('Person'),
        url=lambda meta: (
            meta.request.class_link(PersonFunctionSuggestion) + '?term=%QUERY'
        )
    )

    person_political_affiliation = TypeAheadField(
        label=_('Party or parliamentary group'),
        fieldset=_('Person'),
        url=lambda meta: (
            meta.request.class_link(PersonPoliticalAffiliationSuggestion)
            + '?term=%QUERY'
        )
    )

    person_place = TypeAheadField(
        label=_('Place'),
        fieldset=_('Person'),
        url=lambda meta: (
            meta.request.class_link(PersonPlaceSuggestion) + '?term=%QUERY'
        )
    )

    person_picture = UploadField(
        label=_('Picture'),
        fieldset=_('Person'),
        validators=[
            WhitelistedMimeType({
                'image/jpeg',
                'image/png',
            }),
            FileSizeLimit(1 * 1024 * 1024)
        ]
    )

    video_timestamp = StringField(
        label=_('Video timestamp'),
        fieldset=_('Progress'),
        description='2m1s',
        validators=[
            Optional()
        ],
    )

    text = HtmlField(
        label=_('Text'),
        fieldset=_('Content'),
    )

    motion = HtmlField(
        label=_('Text'),
        fieldset=_('Motion'),
    )

    statement_of_reasons = HtmlField(
        label=_('Text'),
        fieldset=_('Statement of reasons'),
    )

    @property
    def next_number(self):
        query = self.request.session.query(Votum.number)
        query = query.filter(
            Votum.agenda_item_id == self.model.agenda_item.id
        )
        query = query.order_by(desc(Votum.number))
        query = query.limit(1)
        return (query.scalar() or 0) + 1

    def populate_person_choices(self):
        people = PersonCollection(self.request.session).query()
        self.body_font_family_ui.choices = [
            (p, f'{p.first_name} {p.last_name}, {p.function}, {p.political_party}'
             ) for p in people
        ]

    def on_request(self):
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')
        self.populate_person_choices()

    def get_useful_data(self):
        data = super().get_useful_data()
        data['agenda_item_id'] = self.model.agenda_item.id
        return data

    def validate_number(self, field):
        if field.data:
            query = self.request.session.query(Votum)
            query = query.filter(
                Votum.agenda_item_id == self.model.agenda_item.id,
                Votum.number == field.data
            )
            if isinstance(self.model, Votum):
                query = query.filter(Votum.id != self.model.id)
            if query.first():
                raise ValidationError(_('Number already used.'))
