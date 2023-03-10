from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


class PartyPanachageResult(Base, TimestampMixin):

    __tablename__ = 'party_panachage_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election this result belongs to
    election_id = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    #: the election compound this result belongs to
    election_compound_id = Column(
        Text,
        ForeignKey(
            'election_compounds.id', onupdate='CASCADE', ondelete='CASCADE'
        ),
        nullable=True
    )

    # todo: UUID ??

    #: the target this result belongs to, maps to list.id
    target = Column(Text, nullable=False)

    #: the source this result belongs to, maps to list.id
    source = Column(Text, nullable=False)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)
