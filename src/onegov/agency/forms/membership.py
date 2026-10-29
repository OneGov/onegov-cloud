from onegov.agency import _
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import ExtendedPerson
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.utils import coerce_uuid
from sqlalchemy import func
from wtforms.fields import SelectChoice
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable


def duplicates[T](iterable: Iterable[T]) -> set[T]:
    items = set()
    duplicates = set()
    for item in iterable:
        if item in items:
            duplicates.add(item)
        items.add(item)
    return duplicates


def person_id_choices(
    form: MembershipForm,
    field: ChosenSelectField
) -> list[SelectChoice]:
    ambiguous = duplicates(
        name for name, in form.request.session.query(
            func.concat(
                ExtendedPerson.last_name, ' ', ExtendedPerson.first_name
            )
        )
    )

    def title(person: ExtendedPerson) -> str:
        if person.title in ambiguous:
            info = (
                person.phone_direct
                or person.phone
                or person.email
                or person.postal_address
            )
            if info:
                return f'{person.title} ({info})'
            memberships = person.memberships_by_agency
            if memberships:
                return f'{person.title} ({memberships[0].agency.title})'

        return person.title

    return [
        SelectChoice(str(p.id), title(p))
        for p in ExtendedPersonCollection(form.request.session).query()
    ]


class MembershipForm(Form):
    """ Form to edit memberships of an organization. """

    title = StringField(
        label=_('Title'),
        validators=[
            InputRequired()
        ],
    )

    person_id = ChosenSelectField(
        label=_('Person'),
        choices=person_id_choices,
        coerce=coerce_uuid,
        validators=[
            InputRequired()
        ]
    )

    since = StringField(
        label=_('Since'),
    )

    note = StringField(
        label=_('Note'),
    )

    addition = StringField(
        label=_('Addition'),
    )

    prefix = StringField(
        label=_('Prefix'),
    )

    def validate_title(self, field: StringField) -> None:
        if field.data and not field.data.strip():
            raise ValidationError(_('This field is required.'))
