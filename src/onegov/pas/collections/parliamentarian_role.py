from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import ParliamentarianRole


class ParliamentarianRoleCollection(GenericCollection[ParliamentarianRole]):

    @property
    def model_class(self) -> type[ParliamentarianRole]:
        return ParliamentarianRole
