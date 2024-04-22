from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Integer
from uuid import uuid4

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid


class CostOfLivingAdjustment(Base, TimestampMixin):

    __tablename__ = 'pas_colas'

    multiplicator = 10000

    #: Internal ID
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The year
    year: 'Column[int]' = Column(
        Integer,
        nullable=False
    )

    #: The value
    value: 'Column[int]' = Column(
        Integer,
        nullable=False
    )

    @property
    def percentage(self) -> float:
        return self.value / self.multiplicator

    @percentage.setter
    def percentage(self, value: float) -> None:
        self.value = int(value * self.multiplicator)
