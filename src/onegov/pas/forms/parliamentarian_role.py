from onegov.form import move_fields
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.form.utils import coerce_uuid
from onegov.org.forms import ParliamentarianRoleForm
from onegov.parliament.models.parliamentarian_role import PARTY_ROLES
from onegov.pas import _
from onegov.pas.collections import PartyCollection
from onegov.pas.models import Party
from wtforms import SelectChoice


from typing import TYPE_CHECKING


class PASParliamentarianRoleForm(ParliamentarianRoleForm):

    party_id = ChosenSelectField(
        label=_('Political Party'),
        choices=lambda form, value: [SelectChoice('', '-'), *(
            SelectChoice(party_id.hex, name)
            for party_id, name in PartyCollection(form.request.session).query()
            .with_entities(Party.id, Party.name)
        )],
        coerce=coerce_uuid
    )

    party_role = TranslatedSelectField(
        label=_('Party role'),
        choices=[
            SelectChoice(value, label)
            for value, label in PARTY_ROLES.items()
        ],
        default='none'
    )


if not TYPE_CHECKING:
    # Move party field to correct location
    PASParliamentarianRoleForm = move_fields(
        PASParliamentarianRoleForm,
        ('party_id', 'party_role'),
        before='parliamentary_group_id'
    )
