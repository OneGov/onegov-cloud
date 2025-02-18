from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pas import _
from onegov.pas.models.commission import Commission
from onegov.pas.models.parliamentarian import Parliamentarian
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date
    from typing import Literal
    from typing import TypeAlias

    MembershipRole: TypeAlias = Literal[
        'guest',
        'member',
        'extended_member',
        'president',
    ]

ROLES: dict[MembershipRole, str] = {
    'guest': _('Guest'),
    'member': _('Member'),
    'extended_member': _('Extended Member'),
    'president': _('President')
}


class CommissionMembership(Base, TimestampMixin):

    __tablename__ = 'pas_commission_memberships'

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The start date
    start: Column[date | None] = Column(
        Date,
        nullable=True
    )

    #: The end date
    end: Column[date | None] = Column(
        Date,
        nullable=True
    )

    #: The role value
    role: Column[MembershipRole] = Column(
        Enum(
            *ROLES.keys(),  # type:ignore[arg-type]
            name='pas_commission_membership_role'
        ),
        nullable=False,
        default='member'
    )

    #: The role as translated text
    @property
    def role_label(self) -> str:
        return ROLES.get(self.role, '')

    #: the id of the commission
    commission_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('pas_commissions.id'),
        nullable=False
    )

    #: the related commission (which may have any number of memberships)
    commission: relationship[Commission] = relationship(
        Commission,
        back_populates='memberships'
    )

    #: the id of the parliamentarian
    parliamentarian_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('pas_parliamentarians.id'),
        nullable=False
    )

    #: the related parliamentarian (which may have any number of memberships)
    parliamentarian: relationship[Parliamentarian] = relationship(
        Parliamentarian,
        back_populates='commission_memberships'
    )

    def __repr__(self) -> str:
        return (
            f'<CommissionMembership role={self.role}, '
            f'p={self.parliamentarian.title}, commission'
            f'={self.commission.name}'
        )
