from datetime import date
from onegov.core.collection import GenericCollection
from onegov.pas.models import Commission
from sqlalchemy import or_

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing_extensions import Self


class CommissionCollection(GenericCollection[Commission]):

    def __init__(
        self,
        session: 'Session',
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[Commission]:
        return Commission

    def query(self) -> 'Query[Commission]':
        query = super().query()

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
    ) -> 'Self':
        return self.__class__(self.session, active)
