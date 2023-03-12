from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


class PanachageResult(Base, TimestampMixin):

    # todo: remove hits obsolete model after migration

    __tablename__ = 'panachage_results'

    id = Column(UUID, primary_key=True, default=uuid4)

    election_id = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    election_compound_id = Column(
        Text,
        ForeignKey(
            'election_compounds.id', onupdate='CASCADE', ondelete='CASCADE'
        ),
        nullable=True
    )

    target = Column(Text, nullable=False)

    source = Column(Text, nullable=False)

    votes = Column(Integer, nullable=False, default=lambda: 0)
