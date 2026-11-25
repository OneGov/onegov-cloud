from datetime import date
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.form.utils import coerce_uuid
from onegov.org import _
from onegov.parliament.collections import ParliamentarianCollection
from onegov.parliament.collections import ParliamentaryGroupCollection
from onegov.parliament.models.parliamentarian_role import (
    PARLIAMENTARY_GROUP_ROLES,
    PARLIAMENTARIAN_ROLES
)
from wtforms.fields import DateField
from wtforms.fields import SelectChoice
from wtforms.validators import InputRequired
from wtforms.validators import Optional


def parliamentary_group_choices(
    form: Form,
    field: ChosenSelectField
) -> list[SelectChoice]:
    choices = [
        SelectChoice(parliamentary_group.id.hex, parliamentary_group.title)
        for parliamentary_group
        in ParliamentaryGroupCollection(form.request.session).query()
    ]
    choices.insert(0, SelectChoice('', '-'))
    return choices


class ParliamentarianRoleForm(Form):

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
            for value, label in PARLIAMENTARIAN_ROLES.items()
        ],
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
        choices=parliamentary_group_choices,
        coerce=coerce_uuid
    )

    parliamentary_group_role = TranslatedSelectField(
        label=_('Parliamentary group role'),
        choices=[
            SelectChoice(value, label)
            for value, label in PARLIAMENTARY_GROUP_ROLES.items()
        ],
        default='none'
    )
