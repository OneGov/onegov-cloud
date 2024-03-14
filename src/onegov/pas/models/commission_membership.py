from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
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
    from typing_extensions import TypeAlias

    MembershipPosition: TypeAlias = Literal[
        'guest',
        'member',
        'extended',
        'president',
    ]


POSITIONS: dict['MembershipPosition', str] = {
    'guest': _('Guest'),
    'member': _('Member'),
    'extended': _('Extended Member'),
    'president': _('President')
}


class CommissionMembership(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'pas_commission_memberships'

    #: Internal ID
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The start date
    start: 'Column[date|None]' = Column(
        Date,
        nullable=True
    )

    #: The end date
    end: 'Column[date|None]' = Column(
        Date,
        nullable=True
    )

    #: The position value
    position: 'Column[MembershipPosition]' = Column(
        Enum(
            *POSITIONS.keys(),  # type:ignore[arg-type]
            name='pas_commission_membership_position'
        ),
        nullable=False,
        default='member'
    )

    #: The position as translated text
    @property
    def position_label(self) -> str:
        return POSITIONS.get(self.position, '')

    #: the id of the agency
    commission_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('pas_commissions.id'),
        nullable=False
    )

    #: the related commission (which may have any number of memberships)
    commission: 'relationship[Commission]' = relationship(
        Commission,
        back_populates='memberships'
    )

    #: the id of the parliamentarian
    parliamentarian_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('pas_parliamentarians.id'),
        nullable=False
    )

    #: the related parliamentarian (which may have any number of memberships)
    parliamentarian: 'relationship[Parliamentarian]' = relationship(
        Parliamentarian,
        back_populates='commission_memberships'
    )
