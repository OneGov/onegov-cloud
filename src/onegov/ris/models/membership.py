from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin, ContentMixin
from onegov.core.orm.types import UUID
from onegov.ris import _


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from typing import Literal
    from typing import TypeAlias

    from onegov.ris.models.commission import RISCommission
    from onegov.ris.models.parliamentarian import RISParliamentarian

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


class RISCommissionMembership(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'ris_parliamentary_memberships'

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
            name='ris_parliamentary_membership_role'
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
        ForeignKey('ris_commissions.id'),
        nullable=False
    )

    #: the related commission (which may have any number of memberships)
    commission: relationship[RISCommission] = relationship(
        'RISCommission',
        back_populates='memberships'
    )

    #: the id of the parliamentarian
    # NEEDED???
    parliamentarian_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ris_parliamentarians.id'),
        nullable=False
    )

    #: the related parliamentarian (which may have any number of memberships)
    parliamentarian: relationship[RISParliamentarian] = relationship(
        'RISParliamentarian',
        back_populates='commission_memberships'
    )

    def __repr__(self) -> str:
        return (
            f'<ParliamentaryMembership role={self.role}, '
            f'p={self.parliamentarian.title}, '
            f'commission={self.commission.name}'
        )
