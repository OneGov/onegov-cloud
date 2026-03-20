from __future__ import annotations

from uuid import uuid4, UUID

from sqlalchemy import func, Column, ForeignKey, Index, Table, UUID as UUIDType
from sqlalchemy.orm import mapped_column, object_session, relationship, Mapped

from onegov.core.orm import Base


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .translator import Translator


spoken_association_table = Table(
    'spoken_lang_association',
    Base.metadata,
    Column(
        'translator_id',
        UUIDType(as_uuid=True),
        ForeignKey('translators.id'),
        nullable=False
    ),
    Column(
        'lang_id',
        UUIDType(as_uuid=True),
        ForeignKey('languages.id'),
        nullable=False
    )
)

written_association_table = Table(
    'written_lang_association',
    Base.metadata,
    Column(
        'translator_id',
        UUIDType(as_uuid=True),
        ForeignKey('translators.id'),
        nullable=False
    ),
    Column(
        'lang_id',
        UUIDType(as_uuid=True),
        ForeignKey('languages.id'),
        nullable=False
    )
)

monitoring_association_table = Table(
    'monitoring_lang_association',
    Base.metadata,
    Column(
        'translator_id',
        UUIDType(as_uuid=True),
        ForeignKey('translators.id'),
        nullable=False
    ),
    Column(
        'lang_id',
        UUIDType(as_uuid=True),
        ForeignKey('languages.id'),
        nullable=False
    )
)

mother_tongue_association_table = Table(
    'mother_tongue_association',
    Base.metadata,
    Column(
        'translator_id',
        UUIDType(as_uuid=True),
        ForeignKey('translators.id'),
        nullable=False
    ),
    Column(
        'lang_id',
        UUIDType(as_uuid=True),
        ForeignKey('languages.id'),
        nullable=False
    )
)


class Language(Base):

    __tablename__ = 'languages'

    __table_args__ = (
        Index('unique_name', 'name', unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )
    name: Mapped[str]

    @property
    def speakers_count(self) -> int:
        session = object_session(self)
        assert session is not None
        return session.query(
            func.count(spoken_association_table.c.translator_id)
        ).filter(spoken_association_table.c.lang_id == self.id).scalar()

    @property
    def writers_count(self) -> int:
        session = object_session(self)
        assert session is not None
        return session.query(
            func.count(written_association_table.c.translator_id)
        ).filter(written_association_table.c.lang_id == self.id).scalar()

    @property
    def monitors_count(self) -> int:
        session = object_session(self)
        assert session is not None
        return session.query(
            func.count(monitoring_association_table.c.translator_id)
        ).filter(monitoring_association_table.c.lang_id == self.id).scalar()

    @property
    def native_speakers_count(self) -> int:
        session = object_session(self)
        assert session is not None
        return session.query(
            func.count(mother_tongue_association_table.c.translator_id)
        ).filter(mother_tongue_association_table.c.lang_id == self.id).scalar()

    @property
    def deletable(self) -> bool:
        # NOTE: by using boolean logic we can short-circuit and perform
        #       fewer redundant queries. It may be even faster however
        #       to just create a single query with 4 exists subqueries.
        return (
            self.speakers_count == 0
            and self.writers_count == 0
            and self.native_speakers_count == 0
            and self.monitors_count == 0
        )

    mother_tongues: Mapped[list[Translator]] = relationship(
        secondary=mother_tongue_association_table,
        back_populates='mother_tongues'
    )
    speakers: Mapped[list[Translator]] = relationship(
        secondary=spoken_association_table,
        back_populates='spoken_languages'
    )
    writers: Mapped[list[Translator]] = relationship(
        secondary=written_association_table,
        back_populates='written_languages'
    )
    monitors: Mapped[list[Translator]] = relationship(
        secondary=monitoring_association_table,
        back_populates='monitoring_languages'
    )

    def __repr__(self) -> str:
        return self.name
