from __future__ import annotations

from onegov.parliament.collections.party import PartyCollection
from onegov.pas.models import PASParty


class PASPartyCollection(PartyCollection):

    @property
    def model_class(self) -> type[PASParty]:
        return PASParty
