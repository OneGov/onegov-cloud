from uuid import uuid4

from sqlalchemy import Column, Text, Enum

from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable

ADMISSIONS = ('uncertified', 'in_progress', 'certified')

class Translator(Base, ORMSearchable):

    __tablename__ = 'translators'

    es_public = True

    id = Column(UUID, primary_key=True, default=uuid4)

    last_name = Column(Text, nullable=False)
    first_name = Column(Text, nullable=False)

    # Personal-Nr., was genau? generieren, Laufnummer?
    pers_id = Column(Text, nullable=False)

    #: the admission of licence of the translator / Zulassung
    admission_state = Column(
        Enum(*ADMISSIONS, name='admission_state'),
        nullable=False,
        default='preview'
    )

    # Quellensteuer
    withholding_tax = Column(Text)
