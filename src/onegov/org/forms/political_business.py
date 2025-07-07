from __future__ import annotations

from datetime import date
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import TranslatedSelectField
from wtforms.fields import DateField
from onegov.parliament import _
from onegov.parliament.models import Parliamentarian
from onegov.parliament.models import ParliamentaryGroup
from onegov.parliament.models.parliamentarian import RISParliamentarian
from onegov.parliament.models.political_business import (
    POLITICAL_BUSINESS_TYPE,
    POLITICAL_BUSINESS_STATUS
)

from typing import Any


class PoliticalBusinessForm(Form):
    title = StringField(
        label=_('Title'),
        fieldset=_('A'),
        validators=[InputRequired()],
    )

    number = StringField(
        label=_('Number'),
        fieldset=_('A'),
        validators=[Optional()],
    )

    political_business_type = TranslatedSelectField(
        label=_('Type'),
        fieldset=_('A'),
        choices=sorted(POLITICAL_BUSINESS_TYPE.items()),
        validators=[InputRequired()],
    )

    status = TranslatedSelectField(
        label=_('Business Status'),
        fieldset=_('A'),
        choices=sorted(POLITICAL_BUSINESS_STATUS.items()),
        validators=[Optional()],
        default='-',
    )

    entry_date = DateField(
        label=_('Entry Date'),
        fieldset=_('A'),
        validators=[InputRequired()],
        default=date.today,
    )

    selected_participants = ChosenSelectMultipleField(
        label=_('Participants'),
        fieldset=_('A'),
        validators=[Optional()],
        choices=[],
    )

    # depending on selected_participants, for each individual i need to
    # create a PoliticalBusinessParticipation object

    # FIXME : make multiple groups possible ChosenSelectMultipleField
    selected_parliamentary_group_id = ChosenSelectField(
        label=_('Parliamentary Group'),
        fieldset=_('A'),
        validators=[Optional()],
        choices=[],
    )

    @property
    def participants(self) -> list[RISParliamentarian]:
        """ Returns the selected parliamentarians. """

        if not self.selected_participants.data:
            return []

        result = (
            self.request.session.query(RISParliamentarian)
            .filter(
                RISParliamentarian.id.in_(self.selected_participants.data)
            )
            .all()
        )

        return result

    @property
    def parliamentary_group_id(self) -> str | None:
        """ Returns the selected parliamentary group id. """
        if self.selected_parliamentary_group_id.data:
            group = self.request.session.query(ParliamentaryGroup).get(
                self.selected_parliamentary_group_id.data
            )
            return str(group.id) if group else None

        return None

    def on_request(self) -> None:
        self.political_business_type.choices.insert(0, ('', '-'))  # type:ignore[union-attr]
        self.status.choices.insert(0, ('', '-'))  # type:ignore[union-attr]

        parliamentarians = (
            self.request.session.query(RISParliamentarian)
            .filter(RISParliamentarian.active == True)
            .order_by(Parliamentarian.last_name, Parliamentarian.first_name)
            .all()
        )
        self.selected_participants.choices = [
            (str(p.id.hex), p.display_name) for p in parliamentarians
        ]

        groups = (
            self.request.session.query(ParliamentaryGroup)
            .filter(ParliamentaryGroup.end == None)
            .order_by(ParliamentaryGroup.name)
            .all()
        )
        self.selected_parliamentary_group_id.choices = [
            (str(g.id.hex), g.name) for g in groups
        ]

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['participants'] = self.participants
        result['parliamentary_group_id'] = self.parliamentary_group_id
        result.pop('selected_participants', None)
        result.pop('selected_parliamentary_group_id', None)
        return result
