from __future__ import annotations

from collections.abc import Collection
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
from onegov.parliament.models import PoliticalBusiness
from onegov.parliament.models import RISParliamentarian
from onegov.parliament.models import RISParliamentaryGroup
from onegov.parliament.models.political_business import (
    POLITICAL_BUSINESS_TYPE,
    POLITICAL_BUSINESS_STATUS
)

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import uuid


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
    # specify the participation type
    participation_type = ChosenSelectField(
        label=_('Participation Type'),
        fieldset=_('A'),
        validators=[Optional()],
        choices=[
            ('', '-'),
            ('first_signatory', _('First Signatory')),
            ('co_signatory', _('Co-Signatory')),
        ],
        default='co_signatory',
        depends_on=('selected_participants', 'choices')
    )

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

        parliamentarians = (
            self.request.session.query(RISParliamentarian)
            .filter(RISParliamentarian.active)
            .order_by(Parliamentarian.last_name, Parliamentarian.first_name)
            .all()
        )
        self.selected_participants.choices = [
            (str(p.id.hex), p.display_name) for p in parliamentarians
        ]

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
        result['participants'] = self.participants
        result['parliamentary_group_id'] = self.parliamentary_group_id
        result.pop('selected_participants', None)
        result.pop('selected_parliamentary_group_id', None)
        return result

    def populate_obj(
        self,
        obj: object | PoliticalBusiness,
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        print('*** tschupre populate_obj ***')
        super().populate_obj(
            obj,
            exclude={
                'selected_participants',
                'parliamentary_group_id'
            },
            include=include
        )

        obj.parliamentary_group_id = self.parliamentary_group_id  # type:ignore[union-attr]

    def process_obj(self, model: PoliticalBusiness) -> None:  # type:ignore[override]
        print('*** tschupre process_obj ***')
        super().process_obj(model)

        self.parliamentary_group_id = model.parliamentary_group_id
