from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.org import _
from onegov.parliament.collections import ParliamentarianCollection
from onegov.parliament.collections import ParliamentaryGroupCollection
from onegov.parliament.models.parliamentarian_role import (
    PARLIAMENTARY_GROUP_ROLES,
    PARLIAMENTARIAN_ROLES
)
from wtforms.fields import DateField
from wtforms.validators import InputRequired
from wtforms.validators import Optional

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.parliament.models import ParliamentarianRole


class ParliamentarianRoleForm(Form):

    parliamentarian_id = ChosenSelectField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
    )

    role = TranslatedSelectField(
        label=_('Role'),
        choices=list(PARLIAMENTARIAN_ROLES.items()),
        validators=[InputRequired()],
        default='member'
    )

    start = DateField(
        label=_('Start'),
        validators=[Optional()],
        default=date.today
    )

    end = DateField(
        label=_('End'),
        validators=[Optional()],
    )

    parliamentary_group_id = ChosenSelectField(
        label=_('Parliamentary group'),
    )

    parliamentary_group_role = TranslatedSelectField(
        label=_('Parliamentary group role'),
        choices=list(PARLIAMENTARY_GROUP_ROLES.items()),
        default='none'
    )

    def on_request(self) -> None:
        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian
            in ParliamentarianCollection(self.request.session).query()
        ]
        self.parliamentary_group_id.choices = [
            (str(parliamentary_group.id), parliamentary_group.title)
            for parliamentary_group
            in ParliamentaryGroupCollection(self.request.session).query()
        ]
        self.parliamentary_group_id.choices.insert(0, ('', '-'))

    def populate_obj(  # type: ignore[override]
        self,
        obj: ParliamentarianRole,  # type: ignore[override]
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        super().populate_obj(
            obj,
            {'parliamentary_group_id', *(exclude or ())},
            include
        )
        obj.parliamentary_group_id = self.parliamentary_group_id.data or None

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['parliamentary_group_id'] = result.get(
            'parliamentary_group_id') or None
        return result
