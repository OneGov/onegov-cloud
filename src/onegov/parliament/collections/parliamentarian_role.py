from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import ParliamentarianRole


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from uuid import UUID  # ruff:ignore[unused-import]


class ParliamentarianRoleCollection[RoleT: ParliamentarianRole = Any](
    GenericCollection[RoleT, 'UUID']
):

    @property
    def model_class(self) -> type[RoleT]:
        return ParliamentarianRole  # type: ignore[return-value]
