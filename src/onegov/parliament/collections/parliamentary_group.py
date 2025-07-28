from __future__ import annotations

from datetime import date
from onegov.core.collection import GenericCollection
from onegov.parliament.models import ParliamentaryGroup
from sqlalchemy import or_


from typing import Any, TYPE_CHECKING
from typing_extensions import TypeVar
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self

GroupT = TypeVar(
    'GroupT',
    bound=ParliamentaryGroup,
    default=Any
)


class ParliamentaryGroupCollection(GenericCollection[GroupT]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[GroupT]:
        return ParliamentaryGroup  # type: ignore[return-value]

    def query(self) -> Query[GroupT]:
        query = super().query()

        ParliamentaryGroup = self.model_class  # noqa: N806
        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        ParliamentaryGroup.end.is_(None),
                        ParliamentaryGroup.end >= date.today()
                    )
                )
            else:
                query = query.filter(ParliamentaryGroup.end < date.today())

        return query.order_by(ParliamentaryGroup.name)

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
