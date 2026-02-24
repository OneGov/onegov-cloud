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
    from onegov.election_day.models import ElectionResult
    from onegov.election_day.models import List


class ListResult(Base, TimestampMixin):
    """ The election result of a list in a single political entity. """

    __tablename__ = 'list_results'

    #: identifies the list
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    # votes
    votes: Mapped[int] = mapped_column(default=lambda: 0)

    #: the election result id this result belongs to
    election_result_id: Mapped[UUID] = mapped_column(
        ForeignKey('election_results.id', ondelete='CASCADE')
    )

    #: the election result this result belongs to
    election_result: Mapped[ElectionResult] = relationship(
        back_populates='list_results'
    )

    #: the list id this result belongs to
    list_id: Mapped[UUID] = mapped_column(
        ForeignKey('lists.id', ondelete='CASCADE')
    )

    #: the list this result belongs to
    list: Mapped[List] = relationship(
        back_populates='results'
    )
