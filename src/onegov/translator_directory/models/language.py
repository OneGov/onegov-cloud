from __future__ import annotations

from uuid import uuid4

from sqlalchemy import func, Index, Column, Text, Table, ForeignKey
from sqlalchemy.orm import object_session, relationship

from onegov.core.orm import Base
from onegov.core.orm.types import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid

    from .translator import Translator


spoken_association_table = Table(
    'spoken_lang_association',
    Base.metadata,
    Column(
        'translator_id',
        UUID,
        ForeignKey('translators.id'),
        nullable=False),
    Column('lang_id', UUID, ForeignKey('languages.id'), nullable=False)
)

written_association_table = Table(
    'written_lang_association',
    Base.metadata,
    Column(
        'translator_id',
        UUID,
        ForeignKey('translators.id'),
        nullable=False),
    Column('lang_id', UUID, ForeignKey('languages.id'), nullable=False)
)

monitoring_association_table = Table(
    'monitoring_lang_association',
    Base.metadata,
    Column(
        'translator_id',
        UUID,
        ForeignKey('translators.id'),
        nullable=False),
    Column('lang_id', UUID, ForeignKey('languages.id'), nullable=False)
)

mother_tongue_association_table = Table(
    'mother_tongue_association',
    Base.metadata,
    Column(
        'translator_id',
        UUID,
        ForeignKey('translators.id'),
        nullable=False),
    Column('lang_id', UUID, ForeignKey('languages.id'), nullable=False)
)


class Language(Base):

    __tablename__ = 'languages'

    __table_args__ = (
        Index('unique_name', 'name', unique=True),
    )

    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )
    name: Column[str] = Column(Text, nullable=False)

    @property
    def speakers_count(self) -> int:
        session = object_session(self)
        return session.query(
            func.count(spoken_association_table.c.translator_id)
        ).filter(spoken_association_table.c.lang_id == self.id).scalar()

    @property
    def writers_count(self) -> int:
        session = object_session(self)
        return session.query(
            func.count(written_association_table.c.translator_id)
        ).filter(written_association_table.c.lang_id == self.id).scalar()

    @property
    def monitors_count(self) -> int:
        session = object_session(self)
        return session.query(
            func.count(monitoring_association_table.c.translator_id)
        ).filter(monitoring_association_table.c.lang_id == self.id).scalar()

    @property
    def native_speakers_count(self) -> int:
        session = object_session(self)
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

    mother_tongues: relationship[list[Translator]] = relationship(
        'Translator',
        secondary=mother_tongue_association_table,
        back_populates='mother_tongues'
    )
    speakers: relationship[list[Translator]] = relationship(
        'Translator',
        secondary=spoken_association_table,
        back_populates='spoken_languages'
    )
    writers: relationship[list[Translator]] = relationship(
        'Translator',
        secondary=written_association_table,
        back_populates='written_languages'
    )
    monitors: relationship[list[Translator]] = relationship(
        'Translator',
        secondary=monitoring_association_table,
        back_populates='monitoring_languages'
    )

    def __repr__(self) -> str:
        return self.name
