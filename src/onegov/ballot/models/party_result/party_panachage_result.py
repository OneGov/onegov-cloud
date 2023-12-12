from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from sqlalchemy.orm import relationship

    from ..election import ProporzElection
    from ..election_compound import ElectionCompound


class PartyPanachageResult(Base, TimestampMixin):

    __tablename__ = 'party_panachage_results'

    #: identifies the result
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the election this result belongs to
    election_id: 'Column[str | None]' = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    #: the election compound this result belongs to
    election_compound_id: 'Column[str | None]' = Column(
        Text,
        ForeignKey(
            'election_compounds.id', onupdate='CASCADE', ondelete='CASCADE'
        ),
        nullable=True
    )

    #: the party target this result belongs to, maps to party_id
    target: 'Column[str]' = Column(Text, nullable=False)

    #: the party source this result belongs to, maps to party_id; might also
    #: refer to the black list by being empty
    source: 'Column[str]' = Column(Text, nullable=False)

    # votes
    votes: 'Column[int]' = Column(Integer, nullable=False, default=lambda: 0)

    if TYPE_CHECKING:
        # backrefs
        election: relationship[ProporzElection | None]
        election_compound: relationship[ElectionCompound | None]
