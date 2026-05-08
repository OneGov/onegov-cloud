from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import List


class ListPanachageResult(Base, TimestampMixin):

    __tablename__ = 'list_panachage_results'

    #: identifies the result
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the target list id this result belongs to
    target_id: Mapped[UUID] = mapped_column(
        ForeignKey('lists.id', ondelete='CASCADE')
    )

    #: the target list this result belongs to
    target: Mapped[List] = relationship(
        foreign_keys='ListPanachageResult.target_id',
        back_populates='panachage_results'
    )

    #: the source list id this result belongs to, empty if blank list
    source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('lists.id', ondelete='CASCADE')
    )

    #: the source list this result belongs to, empty if blank list
    source: Mapped[List | None] = relationship(
        foreign_keys='ListPanachageResult.source_id',
        back_populates='panachage_results_lost'
    )

    #: the number of votes
    votes: Mapped[int] = mapped_column(default=lambda: 0)
