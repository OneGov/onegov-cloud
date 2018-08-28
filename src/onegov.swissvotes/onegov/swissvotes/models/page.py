from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from sqlalchemy import Column
from sqlalchemy import Text


class TranslatablePage(Base, TimestampMixin):
    """ A page containing translatable content. """

    __tablename__ = 'swissvotes_page'

    id = Column(Text, nullable=False, primary_key=True)

    title_translations = Column(HSTORE, nullable=False)
    title = translation_hybrid(title_translations)

    content_translations = Column(HSTORE, nullable=False)
    content = translation_hybrid(content_translations)
