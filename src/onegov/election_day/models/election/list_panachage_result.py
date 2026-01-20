from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.election_day.models import List


class ListPanachageResult(Base, TimestampMixin):

    __tablename__ = 'list_panachage_results'

    #: identifies the result
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the target list id this result belongs to
    target_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('lists.id', ondelete='CASCADE'),
        nullable=False
    )

    #: the target list this result belongs to
    target: relationship[List] = relationship(
        'List',
        foreign_keys='ListPanachageResult.target_id',
        back_populates='panachage_results'
    )

    #: the source list id this result belongs to, empty if blank list
    source_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('lists.id', ondelete='CASCADE'),
        nullable=True
    )

    #: the source list this result belongs to, empty if blank list
    source: relationship[List] = relationship(
        'List',
        foreign_keys='ListPanachageResult.source_id',
        back_populates='panachage_results_lost'
    )

    #: the number of votes
    votes: Column[int] = Column(Integer, nullable=False, default=lambda: 0)
