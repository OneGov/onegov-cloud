from __future__ import annotations

from datetime import date
from sqlalchemy import or_

from onegov.core.collection import GenericCollection
from onegov.org.models import RISParty, Party


from typing import Any, TYPE_CHECKING
from typing_extensions import TypeVar
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


PartyT = TypeVar(
    'PartyT',
    bound=Party,
    default=Any
)


class PartyCollection(GenericCollection[PartyT]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[PartyT]:
        return Party  # type: ignore[return-value]

    def query(self) -> Query[PartyT]:
        query = super().query()
        model_class = self.model_class
        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        self.model_class.end.is_(None),
                        self.model_class.end >= date.today()
                    )
                )
            else:
                query = query.filter(model_class.end < date.today())
        return query.order_by(model_class.name)

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)


class RISPartyCollection(PartyCollection):

    @property
    def model_class(self) -> type[RISParty]:
        return RISParty
