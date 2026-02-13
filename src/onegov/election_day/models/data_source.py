from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.election_day import _
from onegov.election_day.models.election import Election
from onegov.election_day.models.vote import Vote
from sqlalchemy import desc
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DynamicMapped
from sqlalchemy.orm import Mapped
from uuid import uuid4, UUID


from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
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
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The name of the upload configuration
    name: Mapped[str]

    #: The token used to authenticate
    token: Mapped[UUID] = mapped_column(default=uuid4)

    #: The type of upload
    type: Mapped[UploadType] = mapped_column(
        Enum(
            'vote',
            'majorz',
            'proporz',
            name='type_of_data_source'
        ),
        nullable=False
    )

    #: A configuration may contain n items
    items: DynamicMapped[DataSourceItem] = relationship(
        cascade='all, delete-orphan',
        back_populates='source',
    )

    @property
    def label(self) -> str:
        return dict(UPLOAD_TYPE_LABELS)[self.type]

    def query_candidates(self) -> Query[Election] | Query[Vote]:
        """ Returns a list of available votes or elections matching the
        type of the source. """

        session = object_session(self)
        assert session is not None
        if self.type == 'vote':
            votes = session.query(Vote)
            votes = votes.order_by(
                desc(Vote.date),
                Vote.domain,
                Vote.shortcode,
                Vote.title
            )
            return votes

        elections = session.query(Election).filter(Election.type == self.type)
        elections = elections.order_by(
            desc(Election.date),
            Election.domain,
            Election.shortcode,
            Election.title
        )
        return elections


class DataSourceItem(Base, TimestampMixin):
    """ Stores the configuration of an auto upload. """

    __tablename__ = 'upload_data_source_item'

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the upload configuration result belongs to
    source_id: Mapped[UUID] = mapped_column(ForeignKey(DataSource.id))

    #: the district
    district: Mapped[str | None]

    #: the vote / election number
    number: Mapped[str | None]

    #: the election
    election_id: Mapped[str | None] = mapped_column(
        ForeignKey(Election.id, onupdate='CASCADE')
    )

    election: Mapped[Election | None] = relationship(
        back_populates='data_sources'
    )

    #: the vote
    vote_id: Mapped[str | None] = mapped_column(
        ForeignKey(Vote.id, onupdate='CASCADE'),
    )

    vote: Mapped[Vote | None] = relationship(
        back_populates='data_sources'
    )

    source: Mapped[DataSource] = relationship(
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
