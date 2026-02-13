from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.parliament import _
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import Literal, TypeAlias, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.parliament.models import Commission, Parliamentarian

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

    __tablename__ = 'par_commission_memberships'

    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: Internal ID
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The start date
    start: Mapped[date | None]

    #: The end date
    end: Mapped[date | None]

    #: The role value
    role: Mapped[MembershipRole] = mapped_column(
        Enum(
            *ROLES.keys(),
            name='pas_commission_membership_role'
        ),
        default='member'
    )

    #: The function of the person in this commission
    function: Mapped[str | None]

    #: The role as translated text
    @property
    def role_label(self) -> str:
        return ROLES.get(self.role, '')

    #: the id of the commission
    commission_id: Mapped[UUID] = mapped_column(
        ForeignKey('par_commissions.id')
    )

    #: the related commission (which may have any number of memberships)
    commission: Mapped[Commission] = relationship(
        back_populates='memberships',
        lazy='joined',
    )

    #: the id of the parliamentarian
    parliamentarian_id: Mapped[UUID] = mapped_column(
        ForeignKey('par_parliamentarians.id')
    )

    #: the related parliamentarian (which may have any number of memberships)
    parliamentarian: Mapped[Parliamentarian] = relationship(
        back_populates='commission_memberships',
        lazy='joined',
    )

    def __repr__(self) -> str:
        return (
            f'<CommissionMembership role={self.role}, '
            f'p={self.parliamentarian.title}, commission'
            f'={self.commission.name}'
        )
