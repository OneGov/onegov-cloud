from __future__ import annotations

from onegov.core.collection import GenericCollection
from datetime import date
from sqlalchemy import or_
from onegov.parliament.models.commission_membership import (
    RISCommissionMembership,
    CommissionMembership
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class CommissionMembershipCollection(GenericCollection[CommissionMembership]):

    pass


class RISCommissionMembershipCollection(CommissionMembershipCollection):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[CommissionMembership]:
        return RISCommissionMembership

    def query(self) -> Query[CommissionMembership]:
        query = super().query()

        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        CommissionMembership.end.is_(None),
                        CommissionMembership.end >= date.today()
                    )
                )
            else:
                query = query.filter(CommissionMembership.end < date.today())

        return query

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
