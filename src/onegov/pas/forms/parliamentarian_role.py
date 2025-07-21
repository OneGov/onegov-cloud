from __future__ import annotations

from onegov.form import move_fields
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.org.forms import ParliamentarianRoleForm
from onegov.parliament.models.parliamentarian_role import PARTY_ROLES
from onegov.pas import _
from onegov.pas.collections import PartyCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.pas.models import PASParliamentarianRole


class PASParliamentarianRoleForm(ParliamentarianRoleForm):

    party_id = ChosenSelectField(
        label=_('Political Party'),
    )

    party_role = TranslatedSelectField(
        label=_('Party role'),
        choices=list(PARTY_ROLES.items()),
        default='none'
    )

    def on_request(self) -> None:
        super().on_request()
        self.party_id.choices = [
            (str(party.id), party.title)
            for party
            in PartyCollection(self.request.session).query()
        ]
        self.party_id.choices.insert(0, ('', '-'))

    def populate_obj(  # type: ignore[override]
        self,
        obj: PASParliamentarianRole,  # type: ignore[override]
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        super().populate_obj(
            obj,
            {'party_id', *(exclude or ())},
            include
        )
        obj.party_id = self.party_id.data or None

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['party_id'] = result.get('party_id') or None
        return result


if not TYPE_CHECKING:
    # Move party field to correct location
    PASParliamentarianRoleForm = move_fields(
        PASParliamentarianRoleForm,
        ('party_id', 'party_role'),
        before='parliamentary_group_id'
    )
