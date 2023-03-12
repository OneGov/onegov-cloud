from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


class ListPanachageResult(Base, TimestampMixin):

    __tablename__ = 'ballot_list_panachage_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the target list this result belongs to
    target = Column(
        UUID,
        ForeignKey('lists.id', ondelete='CASCADE'),
        nullable=False
    )

    #: the source this result belongs to, maps to list.list_id; may also refer
    #: to the blank list by being '999'
    source = Column(Text, nullable=False)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)
