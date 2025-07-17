from __future__ import annotations

from onegov.parliament.collections import CommissionCollection
from onegov.parliament.collections import CommissionMembershipCollection
from onegov.parliament.collections import ParliamentarianCollection
from onegov.parliament.collections import ParliamentarianRoleCollection
from onegov.parliament.collections import ParliamentaryGroupCollection
from onegov.parliament.models import Commission
from onegov.parliament.models import CommissionMembership
from onegov.parliament.models import Parliamentarian
from onegov.parliament.models import ParliamentarianRole
from onegov.parliament.models import ParliamentaryGroup
from onegov.search import ORMSearchable
from sedate import utcnow
from sqlalchemy import and_, or_, exists
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property


from typing import Self, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.models import PoliticalBusiness
    from onegov.org.models import PoliticalBusinessParticipation
    from sqlalchemy.orm import Query, Session


class RISCommission(Commission, ORMSearchable):

    __mapper_args__ = {
        'polymorphic_identity': 'ris_commission',
    }

    es_type_name = 'ris_commission'
    es_public = True
    es_properties = {'name': {'type': 'text'}}

    @property
    def es_suggestion(self) -> str:
        return self.name


class RISCommissionCollection(CommissionCollection[RISCommission]):

    @property
    def model_class(self) -> type[RISCommission]:
        return RISCommission


class RISCommissionMembership(CommissionMembership):

    __mapper_args__ = {
        'polymorphic_identity': 'ris_commission_membership'
    }


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
                        RISCommissionMembership.end >= utcnow()
                    )
                )
            else:
                query = query.filter(
                    RISCommissionMembership.end < utcnow()
                )

        return query

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)


class RISParliamentarian(Parliamentarian, ORMSearchable):

    __mapper_args__ = {
        'polymorphic_identity': 'ris_parliamentarian',
    }

    es_type_name = 'ris_parliamentarian'
    es_public = False
    es_properties = {
        'first_name': {'type': 'text'},
        'last_name': {'type': 'text'},
    }

    @property
    def es_suggestion(self) -> tuple[str, ...]:
        return (
            f'{self.first_name} {self.last_name}',
            f'{self.last_name} {self.first_name}'
        )

    #: political businesses participations [0..n]
    political_businesses: relationship[list[PoliticalBusinessParticipation]]
    political_businesses = relationship(
        'PoliticalBusinessParticipation',
        back_populates='parliamentarian',
        lazy='joined'
    )

    @hybrid_property
    def active(self) -> bool:
        # Wil: every parliamentarian is active if in a parliamentary
        # group, which leads to a role
        for role in self.roles:
            if role.end is None or role.end >= utcnow().date():
                return True
        return False

    @active.expression  # type:ignore[no-redef]
    def active(cls):

        return exists().where(
            and_(
                ParliamentarianRole.parliamentarian_id == cls.id,
                or_(
                    ParliamentarianRole.end.is_(None),
                    ParliamentarianRole.end >= utcnow()
                )
            )
        )


class RISParliamentarianCollection(
    ParliamentarianCollection[RISParliamentarian]
):

    @property
    def model_class(self) -> type[RISParliamentarian]:
        return RISParliamentarian


class RISParliamentarianRole(ParliamentarianRole):

    __mapper_args__ = {
        'polymorphic_identity': 'ris_parliamentarian_role',
    }


class RISParliamentarianRoleCollection(
    ParliamentarianRoleCollection[RISParliamentarianRole]
):

    @property
    def model_class(self) -> type[RISParliamentarianRole]:
        return RISParliamentarianRole


class RISParliamentaryGroup(ParliamentaryGroup, ORMSearchable):

    __mapper_args__ = {
        'polymorphic_identity': 'ris_parliamentary_group',
    }

    es_type_name = 'ris_parliamentary_group'
    es_public = True
    es_properties = {'name': {'type': 'text'}}

    political_businesses: relationship[list[PoliticalBusiness]]
    political_businesses = relationship(
        'PoliticalBusiness',
        back_populates='parliamentary_group'
    )

    @property
    def es_suggestion(self) -> str:
        return self.name


class RISParliamentaryGroupCollection(
    ParliamentaryGroupCollection[RISParliamentaryGroup]
):

    @property
    def model_class(self) -> type[RISParliamentaryGroup]:
        return RISParliamentaryGroup
