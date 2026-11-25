from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.form.utils import coerce_uuid
from onegov.org import _
from onegov.parliament.collections import CommissionCollection
from onegov.parliament.collections import ParliamentarianCollection
from onegov.parliament.models.commission_membership import ROLES
from wtforms.fields import DateField
from wtforms.fields import SelectChoice
from wtforms.validators import InputRequired
from wtforms.validators import Optional

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.parliament.models import ParliamentarianRole


def commission_choices(
    form: Form,
    field: ChosenSelectField
) -> list[SelectChoice]:
    choices = [
        SelectChoice(commission.id.hex, commission.title)
        for commission
        in CommissionCollection(form.request.session).query()
    ]
    choices.insert(0, SelectChoice('', '-'))
    return choices


class ParliamentarianCommissionRoleForm(Form):

    parliamentarian_id = ChosenSelectField(
        label=_('Parliamentarian'),
        choices=lambda form, field: [
            SelectChoice(parliamentarian.id.hex, parliamentarian.title)
            for parliamentarian
            in ParliamentarianCollection(form.request.session).query()
        ],
        coerce=coerce_uuid,
        validators=[InputRequired()],
    )

    role = TranslatedSelectField(
        label=_('Role'),
        choices=[
            SelectChoice(value, label)
            for value, label in ROLES.items()
        ],
        validators=[InputRequired()],
        default='member'
    )

    start = DateField(
        label=_('Start'),
        validators=[Optional()],
    )

    end = DateField(
        label=_('End'),
        validators=[Optional()],
    )

    commission_id = ChosenSelectField(
        label=_('Commission'),
        choices=commission_choices,
        coerce=coerce_uuid
    )

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
