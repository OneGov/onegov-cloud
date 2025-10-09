from __future__ import annotations
from datetime import datetime

import pytz

from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TimeField
from onegov.form.fields import TypeAheadField
from onegov.form.forms import NamedFileForm
from onegov.landsgemeinde import _
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import PersonFunctionSuggestion
from onegov.landsgemeinde.models import PersonNameSuggestion
from onegov.landsgemeinde.models import PersonPlaceSuggestion
from onegov.landsgemeinde.models import PersonPoliticalAffiliationSuggestion
from onegov.landsgemeinde.models import Votum
from onegov.landsgemeinde.models.votum import STATES
from onegov.landsgemeinde.utils import timestamp_to_seconds
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
    from wtforms.fields.choices import _Choice


class VotumForm(NamedFileForm):

    request: LandsgemeindeRequest

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
        default=next(iter(STATES.keys()))
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

    start_time = TimeField(
        label=_('Start'),
        fieldset=_('Progress'),
        render_kw={
            'long_description': _(
                'Automatically updated when votum changed to ongoing.'
            ),
            'step': 1
        },
        format='%H:%M:%S',
        validators=[
            Optional()
        ],
    )

    calculated_timestamp = StringField(
        label=_('Calculated video timestamp'),
        fieldset=_('Progress'),
        validators=[
            Optional()
        ],
    )

    video_timestamp = StringField(
        label=_('Manual video timestamp'),
        fieldset=_('Progress'),
        description='1h2m1s',
        render_kw={
            'long_description': _('Overrides the calculated video timestamp.'),
            'step': 1
        },
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
        people_choices: list[_Choice] = [(
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
        self.person_choices.choices = people_choices

    def on_request(self) -> None:
        layout = DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')
        self.request.include('person_votum')
        self.populate_person_choices()
        self.calculated_timestamp.render_kw = {
            'long_description': _(
                'Calculated automatically based on the start time of the '
                'votum and the start time of of the livestream of the '
                '${assembly_type}.',
                mapping={'assembly_type': layout.assembly_type}
            ),
            'readonly': True,
            'step': 1
        }

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        data = super().get_useful_data(exclude={
            'person_choices', 'calculated_timestamp'
        })
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

    def validate_video_timestamp(self, field: StringField) -> None:
        if field.data and timestamp_to_seconds(field.data) is None:
            raise ValidationError(_('Invalid timestamp.'))

    def populate_obj(self, obj: Votum) -> None:  # type:ignore[override]
        super().populate_obj(obj, exclude={'calculated_timestamp'})
        if not obj.start_time and self.state.data == 'ongoing':
            tz = pytz.timezone('Europe/Zurich')
            now = datetime.now(tz=tz).time()
            obj.start_time = now
