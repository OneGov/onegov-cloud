from onegov.election_day import _
from onegov.form.fields import TypeAheadField
from onegov.form.fields import ChosenSelectField
from onegov.form.forms import NamedFileForm
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import PersonFunctionSuggestion
from onegov.landsgemeinde.models import PersonNameSuggestion
from onegov.landsgemeinde.models import PersonPlaceSuggestion
from onegov.landsgemeinde.models import PersonPoliticalAffiliationSuggestion
from onegov.landsgemeinde.models import Votum
from onegov.landsgemeinde.models.votum import STATES
from onegov.org.forms.fields import HtmlField
from onegov.people.collections.people import PersonCollection
from sqlalchemy import func
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import ValidationError


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.request import LandsgemeindeRequest


class VotumForm(NamedFileForm):

    request: 'LandsgemeindeRequest'

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

    person_choices = ChosenSelectField(
        fieldset=_('Person'),
        label=_('Person from person directory'),
        description=_('Choosing a person will overwrite the fields below'),
        default=', , , , ',
        choices=[(', , , , ', '...')]
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

    person_picture = StringField(
        label=_('Picture'),
        fieldset=_('Person'),
        render_kw={'class_': 'image-url'}
    )

    video_timestamp = StringField(
        label=_('Video timestamp'),
        fieldset=_('Progress'),
        description='1h2m1s',
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
    def next_number(self) -> int:
        query = self.request.session.query(func.max(Votum.number))
        query = query.filter(
            Votum.agenda_item_id == self.model.agenda_item.id
        )
        return (query.scalar() or 0) + 1

    def populate_person_choices(self) -> None:
        people = PersonCollection(self.request.session).query()
        people_choices = [(
            (
                f'{p.first_name} {p.last_name}, {p.function}, '
                f'{p.political_party}, {p.location_code_city}, '
                f'{p.picture_url}',
                f'{p.first_name} ' + ', '.join(filter(None, [
                    p.last_name,
                    p.function,
                    p.political_party,
                    p.location_code_city])))
        ) for p in people]
        people_choices.insert(0, (', , , , ', '...'))
        self.person_choices.choices = [
            (v, c) for v, c in people_choices
        ]

    def on_request(self) -> None:
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')
        self.populate_person_choices()
        self.request.include('person_votum')

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        data = super().get_useful_data(exclude={'person_choices'})
        data['agenda_item_id'] = self.model.agenda_item.id
        return data

    def validate_number(self, field: IntegerField) -> None:
        if field.data:
            session = self.request.session
            query = session.query(Votum)
            query = query.filter(
                Votum.agenda_item_id == self.model.agenda_item.id,
                Votum.number == field.data
            )
            if isinstance(self.model, Votum):
                query = query.filter(Votum.id != self.model.id)
            if session.query(query.exists()).scalar():
                raise ValidationError(_('Number already used.'))
