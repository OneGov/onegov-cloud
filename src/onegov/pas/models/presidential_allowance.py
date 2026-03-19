from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.pas import _
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.pas.models import PASParliamentarian
    from onegov.pas.models import SettlementRun


PRESIDENT_YEARLY_ALLOWANCE = 20_000
VICE_PRESIDENT_YEARLY_ALLOWANCE = 5_000

PRESIDENT_QUARTERLY = PRESIDENT_YEARLY_ALLOWANCE // 4  # 5000
VICE_PRESIDENT_QUARTERLY = VICE_PRESIDENT_YEARLY_ALLOWANCE // 4  # 1250

ALLOWANCE_ROLES: dict[str, str] = {
    'president': _('President'),
    'vice_president': _('Vice president'),
}

# FiBu account for presidential allowances
# (amtliche Missionen Kantonsratspräsidiums)
FIBU_KONTO_ALLOWANCE = '3000.30'
LOHNART_ALLOWANCE_NR = '2400'
LOHNART_ALLOWANCE_TEXT = 'Jahreszulage KR-Präsidium'


class PresidentialAllowance(Base, TimestampMixin):
    """Tracks quarterly presidential allowances (Jahreszulage)
    for the president and vice president of the Kantonsrat."""

    __tablename__ = 'pas_presidential_allowances'

    #: Internal ID
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    #: The year
    year: Mapped[int]

    #: The role: 'president' or 'vice_president'
    role: Mapped[str]

    #: The amount in CHF (cents not needed, always whole francs)
    amount: Mapped[int]

    #: The id of the parliamentarian
    parliamentarian_id: Mapped[UUID] = mapped_column(
        ForeignKey('par_parliamentarians.id'),
    )

    #: The parliamentarian
    parliamentarian: Mapped[PASParliamentarian] = relationship()

    #: Optional link to the settlement run this belongs to
    settlement_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('pas_settlements.id'),
        nullable=True,
    )

    #: The settlement run
    settlement_run: Mapped[SettlementRun | None] = relationship()

    @property
    def role_label(self) -> str:
        return ALLOWANCE_ROLES.get(self.role, '')

    def __repr__(self) -> str:
        return (
            f'<PresidentialAllowance {self.year}'
            f' {self.role} {self.amount}>'
        )
