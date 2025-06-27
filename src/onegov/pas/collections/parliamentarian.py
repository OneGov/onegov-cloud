from __future__ import annotations

from onegov.parliament.collections import ParliamentarianCollection
from onegov.pas.models import PASParliamentarian


class PASParliamentarianCollection(ParliamentarianCollection):

    @property
    def model_class(self) -> type[PASParliamentarian]:
        return PASParliamentarian
