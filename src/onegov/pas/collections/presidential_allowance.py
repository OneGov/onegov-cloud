from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.pas.models.presidential_allowance import (
    PresidentialAllowance,
)
from sqlalchemy.orm import joinedload

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from uuid import UUID


class PresidentialAllowanceCollection(
    GenericCollection[PresidentialAllowance]
):

    def __init__(
        self,
        session: Session,
        settlement_run_id: UUID | None = None,
    ):
        super().__init__(session)
        self.settlement_run_id = settlement_run_id

    @property
    def model_class(self) -> type[PresidentialAllowance]:
        return PresidentialAllowance

    def query(self) -> Query[PresidentialAllowance]:
        query = (
            super()
            .query()
            .options(
                joinedload(PresidentialAllowance.parliamentarian),
                joinedload(PresidentialAllowance.settlement_run),
            )
        )
        if self.settlement_run_id is not None:
            query = query.filter(
                PresidentialAllowance.settlement_run_id
                == self.settlement_run_id
            )
        return query.order_by(
            PresidentialAllowance.role,
            PresidentialAllowance.created,
        )

    def for_settlement_run(
        self, settlement_run_id: UUID
    ) -> PresidentialAllowanceCollection:
        return self.__class__(
            self.session,
            settlement_run_id=settlement_run_id,
        )
