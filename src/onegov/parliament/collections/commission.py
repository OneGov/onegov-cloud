from __future__ import annotations

from datetime import date
from onegov.core.collection import GenericCollection
from onegov.parliament.models import Commission
from sqlalchemy import or_


from typing import Any, TYPE_CHECKING
from typing_extensions import TypeVar
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self

CommissionT = TypeVar('CommissionT', bound=Commission, default=Any)


class CommissionCollection(GenericCollection[CommissionT]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[CommissionT]:
        return Commission  # type: ignore[return-value]

    def query(self) -> Query[CommissionT]:
        query = super().query()

        Commission = self.model_class  # noqa: N806
        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        Commission.end.is_(None),
                        Commission.end >= date.today()
                    )
                )
            else:
                query = query.filter(Commission.end < date.today())

        return query.order_by(Commission.name)

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
