from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Boolean, Column, Date, Text
from sqlalchemy.ext.hybrid import hybrid_property
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date
    from onegov.core.orm.mixins import dict_property


class SettlementRun(Base, ContentMixin, TimestampMixin, ORMSearchable):
    """ Abrechnungslauf """

    __tablename__ = 'pas_settlements'

    es_public = False
    es_properties = {'name': {'type': 'text', 'weight': 'A'}}

    @property
    def es_suggestion(self) -> str:
        return self.name

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name
    name: Column[str] = Column(
        Text,
        nullable=False
    )

    #: The start date
    start: Column[date] = Column(
        Date,
        nullable=False
    )

    #: The end date
    end: Column[date] = Column(
        Date,
        nullable=False
    )

    #: Whether this settlement run is closed
    closed: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: The description
    description: dict_property[str | None] = content_property()

    if TYPE_CHECKING:
        active: Column[bool]
    else:
        @hybrid_property
        def active(self) -> bool:
            return not self.closed

        @active.setter
        def active(self, value: bool) -> None:
            self.closed = not value

        @active.expression
        def active(cls):
            return ~cls.closed

    @classmethod
    def get_run_number_for_year(cls, input_date: date) -> int:
        """
        Computes the run number for a given date within a year.

        As per customer requirement: No rule mandates 4 payments yearly,
        but wages must be reported by the 10th.

        Run breakdown:
        - Q1: January to March
        - Q2: April to June
        - Q3: July to September
        - Q4: October to November
        - Q5: December

        Why 5 runs?
        The decision to split the fourth quarter ensures that settlement
        runs are confined to a single calendar year. This avoids situations
        where a settlement overlaps into two different years, which could
        cause issues due to differing cost-of-living adjustments (COLA)
        applicable to each year. Handling settlements across two fiscal years
        would increase complexity.

        Thus, we have 5 yearly runs.
        """
        month = input_date.month
        if 1 <= month <= 3:  # January to March
            return 1
        elif 4 <= month <= 6:  # April to June
            return 2
        elif 7 <= month <= 9:  # July to September
            return 3
        elif 10 <= month <= 11:  # October to November
            return 4
        elif month == 12:      # December
            return 5
        else:
            raise ValueError(
                f'Invalid month: {month}. Date must be within a valid year.'
            )

    def __repr__(self) -> str:
        return f'<SettlementRun {self.name} {self.start} {self.end} >'
