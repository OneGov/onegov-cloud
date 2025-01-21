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
    from onegov.election_day.models import Candidate
    from onegov.election_day.models import ElectionResult
    from onegov.election_day.models import List


class CandidatePanachageResult(Base, TimestampMixin):

    __tablename__ = 'candidate_panachage_results'

    #: identifies the result
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the election result id this result belongs to
    election_result_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('election_results.id', ondelete='CASCADE'),
        nullable=False
    )

    #: the election result this result belongs to
    election_result: relationship[ElectionResult] = relationship(
        'ElectionResult',
        back_populates='candidate_panachage_results'
    )

    #: the candidate id this result belongs to
    target_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('candidates.id', ondelete='CASCADE'),
        nullable=False
    )

    #: the candidate this result belongs to
    candidate: relationship[Candidate] = relationship(
        'Candidate',
        back_populates='panachage_results'
    )

    #: the list id this result belongs to, empty in case of the blank list
    source_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('lists.id', ondelete='CASCADE'),
        nullable=True
    )

    #: the list id this result belongs to, empty in case of the blank list
    list: relationship[List] | None = relationship(
        'List',
        back_populates='candidate_panachage_results'
    )

    #: the number of votes
    votes: Column[int] = Column(Integer, nullable=False, default=lambda: 0)
