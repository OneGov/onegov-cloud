from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.election_day.models.election.list import List
from onegov.election_day.models.mixins import summarized_property
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DynamicMapped
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import ProporzElection
    from sqlalchemy.sql import ColumnElement


class ListConnection(Base, TimestampMixin):

    """ A list connection. """

    __tablename__ = 'list_connections'

    #: internal id of the list
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: external id of the list
    connection_id: Mapped[str]

    #: the election id this result belongs to
    election_id: Mapped[str | None] = mapped_column(
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
    )

    #: the election this result belongs to
    election: Mapped[ProporzElection] = relationship(
        back_populates='list_connections'
    )

    #: ID of the parent list connection
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('list_connections.id')
    )

    # the parent
    parent: Mapped[ListConnection] = relationship(
        back_populates='children',
        remote_side='ListConnection.id'
    )

    #: a list connection contains n lists
    lists: Mapped[list[List]] = relationship(
        cascade='all, delete-orphan',
        back_populates='connection',
        order_by='List.list_id'
    )

    #: a list connection contains n sub-connection
    children: DynamicMapped[ListConnection] = relationship(
        cascade='all, delete-orphan',
        back_populates='parent',
        order_by='ListConnection.connection_id'
    )

    @property
    def total_votes(self) -> int:
        """ Returns the total number of votes. """

        return self.votes + sum(child.total_votes for child in self.children)

    @property
    def total_number_of_mandates(self) -> int:
        """ Returns the total number of mandates. """

        return self.number_of_mandates + sum(
            child.total_number_of_mandates for child in self.children
        )

    #: the total votes
    votes = summarized_property('votes')

    #: the total number of mandates
    number_of_mandates = summarized_property('number_of_mandates')

    def aggregate_results(self, attribute: str) -> int:
        """ Gets the sum of the given attribute from the results. """

        return sum(getattr(list, attribute) for list in self.lists)

    @classmethod
    def aggregate_results_expression(
        cls,
        attribute: str
    ) -> ColumnElement[int]:
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select(
            func.coalesce(
                func.sum(getattr(List, attribute)),
                0
            )
        )
        expr = expr.where(List.connection_id == cls.id)
        return expr.label(attribute)
