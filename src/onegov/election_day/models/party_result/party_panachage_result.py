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
    from onegov.election_day.models import ProporzElection
    from onegov.election_day.models import ElectionCompound


class PartyPanachageResult(Base, TimestampMixin):

    __tablename__ = 'party_panachage_results'

    #: identifies the result
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the election id this result belongs to
    election_id: Mapped[str | None] = mapped_column(
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE')
    )

    #: the election this result belongs to
    election: Mapped[ProporzElection | None] = relationship(
        back_populates='party_panachage_results'
    )

    #: the election compound id this result belongs to
    election_compound_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            'election_compounds.id', onupdate='CASCADE', ondelete='CASCADE'
        )
    )

    #: the election compound this result belongs to
    election_compound: Mapped[ElectionCompound | None] = relationship(
        back_populates='party_panachage_results'
    )

    #: the party target this result belongs to, maps to party_id
    target: Mapped[str]

    #: the party source this result belongs to, maps to party_id; might also
    #: refer to the black list by being empty
    source: Mapped[str]

    # votes
    votes: Mapped[int] = mapped_column(default=lambda: 0)
