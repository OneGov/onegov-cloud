from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.election_day import _
from onegov.election_day.models.election import Election
from onegov.election_day.models.vote import Vote
from sqlalchemy import Column
from sqlalchemy import desc
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.core.types import AppenderQuery
    from sqlalchemy.orm import Query
    from typing import Literal
    from typing import TypeAlias

    UploadType: TypeAlias = Literal['vote', 'proporz', 'majorz']


UPLOAD_TYPE_LABELS = (
    ('vote', _('Vote')),
    ('proporz', _('Election based on proportional representation')),
    ('majorz', _('Election based on the simple majority system')),
)


class DataSource(Base, TimestampMixin):
    """ Stores the data source of an upload. """

    __tablename__ = 'upload_data_source'

    #: Identifies the data source
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The name of the upload configuration
    name: Column[str] = Column(Text, nullable=False)

    #: The token used to authenticate
    token: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        nullable=False,
        default=uuid4
    )

    #: The type of upload
    type: Column[UploadType] = Column(
        Enum(  # type:ignore[arg-type]
            'vote',
            'majorz',
            'proporz',
            name='type_of_data_source'
        ),
        nullable=False
    )

    #: A configuration may contain n items
    items: relationship[AppenderQuery[DataSourceItem]] = relationship(
        'DataSourceItem',
        cascade='all, delete-orphan',
        lazy='dynamic',
        back_populates='source',
    )

    @property
    def label(self) -> str:
        return dict(UPLOAD_TYPE_LABELS)[self.type]

    def query_candidates(self) -> Query[Election | Vote]:
        """ Returns a list of available votes or elections matching the
        type of the source. """

        session = object_session(self)
        if self.type == 'vote':
            query = session.query(Vote)
            query = query.order_by(
                desc(Vote.date),
                Vote.domain,
                Vote.shortcode,
                Vote.title
            )
            return query

        query = session.query(Election).filter(Election.type == self.type)
        query = query.order_by(
            desc(Election.date),
            Election.domain,
            Election.shortcode,
            Election.title
        )
        return query


class DataSourceItem(Base, TimestampMixin):
    """ Stores the configuration of an auto upload. """

    __tablename__ = 'upload_data_source_item'

    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the upload configuration result belongs to
    source_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(DataSource.id),
        nullable=False
    )

    #: the district
    district: Column[str | None] = Column(Text, nullable=True)

    #: the vote / election number
    number: Column[str | None] = Column(Text, nullable=True)

    #: the election
    election_id: Column[str | None] = Column(
        Text,
        ForeignKey(Election.id, onupdate='CASCADE'),
        nullable=True
    )

    election: relationship[Election | None] = relationship(
        'Election',
        back_populates='data_sources'
    )

    #: the vote
    vote_id: Column[str | None] = Column(
        Text,
        ForeignKey(Vote.id, onupdate='CASCADE'),
        nullable=True
    )

    vote: relationship[Vote | None] = relationship(
        'Vote',
        back_populates='data_sources'
    )

    source: relationship[DataSource] = relationship(
        DataSource,
        back_populates='items'
    )

    @property
    def item(self) -> Election | Vote | None:
        """ Returns the vote or election. """
        if self.source.type == 'vote':
            return self.vote
        else:
            return self.election

    @property
    def name(self) -> str:
        item = self.item
        if item:
            return item.title or ''
        return ''
