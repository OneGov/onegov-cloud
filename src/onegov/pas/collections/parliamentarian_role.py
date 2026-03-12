from __future__ import annotations

from onegov.parliament.collections import ParliamentarianRoleCollection
from onegov.pas.models import PASParliamentarianRole


class PASParliamentarianRoleCollection(
    ParliamentarianRoleCollection[PASParliamentarianRole]
):

    @property
    def model_class(self) -> type[PASParliamentarianRole]:
        return PASParliamentarianRole
