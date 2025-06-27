from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import ParliamentarianRole
from onegov.parliament.models import RISParliamentarianRole


class ParliamentarianRoleCollection(GenericCollection[ParliamentarianRole]):

    @property
    def model_class(self) -> type[ParliamentarianRole]:
        return ParliamentarianRole


class RISParliamentarianRoleCollection(ParliamentarianRoleCollection):

    @property
    def model_class(self) -> type[RISParliamentarianRole]:
        return RISParliamentarianRole
