from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import ParliamentarianRole


from typing import Any


class ParliamentarianRoleCollection[RoleT: ParliamentarianRole = Any](
    GenericCollection[RoleT]
):

    @property
    def model_class(self) -> type[RoleT]:
        return ParliamentarianRole  # type: ignore[return-value]
