from uuid import uuid4

from sqlalchemy import Index, Column, Text, Table, ForeignKey
from sqlalchemy.orm import object_session

from onegov.core.orm import Base
from onegov.core.orm.types import UUID


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

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)

    @property
    def speakers_count(self):
        session = object_session(self)
        return session.query(
            spoken_association_table).filter_by(lang_id=self.id).count()

    @property
    def writers_count(self):
        session = object_session(self)
        return session.query(
            written_association_table).filter_by(lang_id=self.id).count()

    @property
    def native_speakers_count(self):
        """Having it as mother tongue..."""
        session = object_session(self)
        return session.query(
            mother_tongue_association_table).filter_by(lang_id=self.id).count()
