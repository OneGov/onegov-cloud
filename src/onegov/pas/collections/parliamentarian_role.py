from __future__ import annotations

from onegov.parliament.collections import ParliamentarianRoleCollection
from onegov.pas.models import PASParliamentarianRole


class PASParliamentarianRoleCollection(ParliamentarianRoleCollection):

    @property
    def model_class(self) -> type[PASParliamentarianRole]:
        return PASParliamentarianRole
