from __future__ import annotations

from onegov.agency import _
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import ExtendedPerson
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from sqlalchemy import func
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TypeVar

    _T = TypeVar('_T')


def duplicates(iterable: Iterable[_T]) -> set[_T]:
    items = set()
    duplicates = set()
    for item in iterable:
        if item in items:
            duplicates.add(item)
        items.add(item)
    return duplicates


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
        choices=[],
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

    def on_request(self) -> None:

        ambiguous = duplicates(
            name for name, in self.request.session.query(
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

        self.person_id.choices = [
            (str(p.id), title(p))
            for p in ExtendedPersonCollection(self.request.session).query()
        ]
