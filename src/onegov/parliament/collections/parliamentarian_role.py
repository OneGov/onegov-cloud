from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import ParliamentarianRole
from onegov.parliament.models import RISParliamentarianRole


from typing import Any
from typing_extensions import TypeVar

RoleT = TypeVar(
    'RoleT',
    bound=ParliamentarianRole,
    default=Any
)


class ParliamentarianRoleCollection(GenericCollection[RoleT]):

    @property
    def model_class(self) -> type[RoleT]:
        return ParliamentarianRole  # type: ignore[return-value]


class RISParliamentarianRoleCollection(
    ParliamentarianRoleCollection[RISParliamentarianRole]
):

    @property
    def model_class(self) -> type[RISParliamentarianRole]:
        return RISParliamentarianRole
