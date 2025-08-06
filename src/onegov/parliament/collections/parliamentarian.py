from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import Parliamentarian

from typing import Any, TYPE_CHECKING
from typing_extensions import TypeVar
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


ParliamentarianT = TypeVar(
    'ParliamentarianT',
    bound=Parliamentarian,
    default=Any
)


class ParliamentarianCollection(GenericCollection[ParliamentarianT]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[ParliamentarianT]:
        return Parliamentarian  # type: ignore[return-value]

    def query(self) -> Query[ParliamentarianT]:
        query = super().query()

        Parliamentarian = self.model_class  # noqa: N806
        if self.active is not None:
            if self.active:
                query = query.filter(Parliamentarian.active == True)
            else:
                query = query.filter(Parliamentarian.active == False)

        return query.order_by(
            Parliamentarian.last_name,
            Parliamentarian.first_name
        ).distinct()

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
