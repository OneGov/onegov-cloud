from __future__ import annotations

from onegov.core.collection import GenericCollection
from datetime import date
from sqlalchemy import or_
from onegov.org.models.commission_membership import (
    RISCommissionMembership,
    CommissionMembership
)

from typing import TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self

MembershipT = TypeVar('MembershipT', bound=CommissionMembership)


class CommissionMembershipCollection(GenericCollection[MembershipT]):
    pass


class RISCommissionMembershipCollection(
    CommissionMembershipCollection[RISCommissionMembership]
):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[RISCommissionMembership]:
        return RISCommissionMembership

    def query(self) -> Query[RISCommissionMembership]:
        query = super().query()

        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        RISCommissionMembership.end.is_(None),
                        RISCommissionMembership.end >= date.today()
                    )
                )
            else:
                query = query.filter(
                    RISCommissionMembership.end < date.today()
                )

        return query

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
