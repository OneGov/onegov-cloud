from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Text
from uuid import uuid4


class Parliamentarian(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'pas_parliamentarians'

    es_public = False
    es_properties = {
        'first_name': {'type': 'text'},
        'last_name': {'type': 'text'},
    }

    @property
    def es_suggestion(self) -> tuple[str, ...]:
        return (
            f'{self.first_name} {self.last_name}',
            f'{self.last_name} {self.first_name}'
        )

    #: Internal ID
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the first name
    first_name = Column(Text, nullable=False)

    #: the last name
    last_name = Column(Text, nullable=False)

    # todo:
    # Grundeigenschaften
    # Personalnummer
    # Vertragsnummer
    # Geschlecht
    # Vorname
    # Nachname
    # Bild
    # etc.
