from __future__ import annotations

from collections.abc import Collection
from datetime import date
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from wtforms.fields import DateField
from onegov.org import _
from onegov.org.collections.political_business_participant import (
    PoliticalBusinessParticipationCollection
)
from onegov.org.models import Parliamentarian
from onegov.org.models import PoliticalBusiness
from onegov.org.models import PoliticalBusinessParticipation
from onegov.org.models import RISParliamentarian
from onegov.org.models import RISParliamentaryGroup
from onegov.org.models.political_business import (
    POLITICAL_BUSINESS_TYPE,
    POLITICAL_BUSINESS_STATUS
)

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import uuid


class PoliticalBusinessForm(Form):
    title = StringField(
        label=_('Title'),
        validators=[InputRequired()],
    )

    number = StringField(
        label=_('Number'),
        validators=[Optional()],
    )

    political_business_type = TranslatedSelectField(
        label=_('Type'),
        choices=sorted(POLITICAL_BUSINESS_TYPE.items()),
        validators=[InputRequired()],
    )

    status = TranslatedSelectField(
        label=_('Business Status'),
        choices=sorted(POLITICAL_BUSINESS_STATUS.items()),
        validators=[InputRequired()],
        default='-',
    )

    entry_date = DateField(
        label=_('Entry Date'),
        validators=[InputRequired()],
        default=date.today,
    )

    # FIXME : make multiple groups possible ChosenSelectMultipleField
    selected_parliamentary_group_id = ChosenSelectField(
        label=_('Parliamentary Group'),
        validators=[Optional()],
        choices=[],
    )

    @property
    def parliamentary_group_id(self) -> str | None:
        """ Returns the selected parliamentary group id. """
        if self.selected_parliamentary_group_id.data:
            group = self.request.session.query(RISParliamentaryGroup).get(
                self.selected_parliamentary_group_id.data
            )
            return str(group.id) if group else None

        return None

    @parliamentary_group_id.setter
    def parliamentary_group_id(self, value: uuid.UUID | None) -> None:
        """ Sets the selected parliamentary group id. """
        if value:
            group = (
                self.request.session.query(RISParliamentaryGroup).get(value))
            self.selected_parliamentary_group_id.data = (
                group.id.hex) if group else None
        else:
            self.selected_parliamentary_group_id.data = None

    def on_request(self) -> None:
        self.political_business_type.choices.insert(0, ('', '-'))  # type:ignore[union-attr]
        self.status.choices.insert(0, ('', '-'))  # type:ignore[union-attr]

        groups = (
            self.request.session.query(RISParliamentaryGroup)
            .filter(RISParliamentaryGroup.end == None)
            .order_by(RISParliamentaryGroup.name)
            .all()
        )
        self.selected_parliamentary_group_id.choices = [
            (str(g.id.hex), g.name) for g in groups
        ]
        self.selected_parliamentary_group_id.choices.insert(0, ('', '-'))

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['parliamentary_group_id'] = self.parliamentary_group_id
        result.pop('selected_participants', None)
        result.pop('selected_parliamentary_group_id', None)
        print('*** tschupre get_useful_data', result)
        return result

    def populate_obj(
        self,
        obj: object | PoliticalBusiness,
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        print('*** tschupre populate_obj PoliticalBusinessForm', obj)
        super().populate_obj(
            obj,
            exclude={
                'parliamentary_group_id'
            },
            include=include
        )

        obj.parliamentary_group_id = self.parliamentary_group_id  # type:ignore[union-attr]

        previous_ids_hex = [
            participation.parliamentarian_id.hex
            for participation in obj.participants
        ]
        data_ids_hex = []

        # handle selection of participants of participants
        parliamentarians = self.request.session.query(RISParliamentarian)
        for participation in self.data.get('participants', []):
            person_id_hex = participation.get('person')
            role = participation.get('role')

            if person_id_hex:
                data_ids_hex.append(person_id_hex)

            if person_id_hex and person_id_hex not in previous_ids_hex:
                parliamentarian = (
                    parliamentarians
                    .filter(Parliamentarian.id == person_id_hex)
                    .first()
                )
                obj.participants.append(
                    PoliticalBusinessParticipation(
                        political_business_id=obj.id,
                        parliamentarian_id=parliamentarian.id,
                        participant_type=role,
                    )
                )

        # handle deselection of participants
        collection = (
            PoliticalBusinessParticipationCollection(self.request.session))
        for participation in obj.participants:
            id = participation.parliamentarian_id.hex

            if id in previous_ids_hex and id not in data_ids_hex:
                collection.delete(participation)

    def process_obj(self, model: PoliticalBusiness) -> None:  # type:ignore[override]
        print('*** tschupre process_obj PoliticalBusinessForm')
        super().process_obj(model)

        self.parliamentary_group_id = model.parliamentary_group_id

        ## moved to BusinessParticipationField::process
        # self.people = [
        #     {
        #         'person': str(participant.id),
        #         'role': participant.role
        #     }
        #     for participant in model.participations
        # ]
        # print('*** tschupre process_obj people', self.data['people'])