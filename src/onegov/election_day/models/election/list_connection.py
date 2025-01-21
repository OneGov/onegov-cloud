from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.election_day.models.election.list import List
from onegov.election_day.models.mixins import summarized_property
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.core.types import AppenderQuery
    from onegov.election_day.models import ProporzElection
    from sqlalchemy.sql import ColumnElement


class ListConnection(Base, TimestampMixin):

    """ A list connection. """

    __tablename__ = 'list_connections'

    #: internal id of the list
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: external id of the list
    connection_id: Column[str] = Column(Text, nullable=False)

    #: the election id this result belongs to
    election_id: Column[str | None] = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    #: the election this result belongs to
    election: relationship[ProporzElection] = relationship(
        'ProporzElection',
        back_populates='list_connections'
    )

    #: ID of the parent list connection
    parent_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('list_connections.id'),
        nullable=True
    )

    # the parent
    parent: relationship[ListConnection] = relationship(
        'ListConnection',
        back_populates='children',
        remote_side='ListConnection.id'
    )

    #: a list connection contains n lists
    lists: relationship[list[List]] = relationship(
        'List',
        cascade='all, delete-orphan',
        back_populates='connection',
        order_by='List.list_id'
    )

    #: a list connection contains n sub-connection
    children: relationship[AppenderQuery[ListConnection]] = relationship(
        'ListConnection',
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

        expr = select([
            func.coalesce(
                func.sum(getattr(List, attribute)),
                0
            )
        ])
        expr = expr.where(List.connection_id == cls.id)
        return expr.label(attribute)
