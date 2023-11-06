from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from sqlalchemy.orm import relationship

    from .candidate import Candidate
    from .election_result import ElectionResult
    from .list import List


class CandidatePanachageResult(Base, TimestampMixin):

    __tablename__ = 'candidate_panachage_results'

    #: identifies the result
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the election result this result belongs to
    election_result_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('election_results.id', ondelete='CASCADE'),
        nullable=False
    )

    #: the target/candidate this result belongs to
    target_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('candidates.id', ondelete='CASCADE'),
        nullable=False
    )

    #: the source/list this result belongs to, may be empty in case of the
    #: blank list
    source_id: 'Column[uuid.UUID | None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('lists.id', ondelete='CASCADE'),
        nullable=True
    )

    #: the number of votes
    votes: 'Column[int]' = Column(Integer, nullable=False, default=lambda: 0)

    if TYPE_CHECKING:
        # backrefs
        election_result: relationship[ElectionResult]
        candidate: relationship[Candidate]
        list: relationship[List | None]
