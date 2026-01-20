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


class CandidateResult(Base, TimestampMixin):
    """ The election result of a candidate in a single political entity. """

    __tablename__ = 'candidate_results'

    #: identifies the candidate result
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    # votes
    votes: Column[int] = Column(Integer, nullable=False, default=lambda: 0)

    #: the election result id this result belongs to
    election_result_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('election_results.id', ondelete='CASCADE'),
        nullable=False
    )

    #: the election result this result belongs to
    election_result: relationship[ElectionResult] = relationship(
        'ElectionResult',
        back_populates='candidate_results'
    )

    #: the candidate id this result belongs to
    candidate_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('candidates.id', ondelete='CASCADE'),
        nullable=False
    )

    #: the candidate this result belongs to
    candidate: relationship[Candidate] = relationship(
        'Candidate',
        back_populates='results'
    )
