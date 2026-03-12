from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.org import _
from onegov.parliament.collections import CommissionCollection
from onegov.parliament.collections import ParliamentarianCollection
from onegov.parliament.models.commission_membership import ROLES
from wtforms.fields import DateField
from wtforms.validators import InputRequired
from wtforms.validators import Optional

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.parliament.models import ParliamentarianRole


class ParliamentarianCommissionRoleForm(Form):

    parliamentarian_id = ChosenSelectField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
    )

    role = TranslatedSelectField(
        label=_('Role'),
        choices=list(ROLES.items()),
        validators=[InputRequired()],
        default='member'
    )

    start = DateField(
        label=_('Start'),
        validators=[InputRequired()],
        default=date.today
    )

    end = DateField(
        label=_('End'),
        validators=[Optional()],
    )

    commission_id = ChosenSelectField(
        label=_('Commission'),
    )

    def on_request(self) -> None:
        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian
            in ParliamentarianCollection(self.request.session).query()
        ]
        self.commission_id.choices = [
            (str(commission.id), commission.title)
            for commission
            in CommissionCollection(self.request.session).query()
        ]
        self.commission_id.choices.insert(0, ('', '-'))

    def populate_obj(  # type: ignore[override]
        self,
        obj: ParliamentarianRole,  # type: ignore[override]
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        super().populate_obj(
            obj,
            {*(exclude or ())},
            include
        )

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        return result
