from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.abstract import MoveDirection
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from onegov.file import AssociatedFiles
from onegov.file import File
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import object_session


class TranslatablePageFile(File):
    """ An attachment to a translatable content page. """

    __mapper_args__ = {'polymorphic_identity': 'swissvotes_page'}

    @property
    def locale(self):
        return self.name.split('-')[0]

    @property
    def filename(self):
        return self.reference.filename


class TranslatablePage(Base, TimestampMixin, AssociatedFiles):
    """ A page containing translatable content. """

    __tablename__ = 'swissvotes_page'

    id = Column(Text, nullable=False, primary_key=True)

    title_translations = Column(HSTORE, nullable=False)
    title = translation_hybrid(title_translations)

    content_translations = Column(HSTORE, nullable=False)
    content = translation_hybrid(content_translations)

    order = Column(Integer, default=2 ** 16)

    @property
    def siblings(self):
        query = object_session(self).query(TranslatablePage)
        query = query.order_by(TranslatablePage.order)
        return query


class TranslatablePageMove(object):
    """ Represents a single move of a page. """

    def __init__(self, session, subject_id, target_id, direction):
        self.session = session
        self.subject_id = subject_id
        self.target_id = target_id
        self.direction = direction

    @classmethod
    def for_url_template(cls):
        return cls(
            session=None,
            subject_id='{subject_id}',
            target_id='{target_id}',
            direction='{direction}'
        )

    def execute(self):
        from onegov.swissvotes.collections import TranslatablePageCollection

        pages = TranslatablePageCollection(self.session)
        subject = pages.by_id(self.subject_id)
        target = pages.by_id(self.target_id)
        if subject and target and subject != target:
            pages.move(
                subject=subject,
                target=target,
                direction=getattr(MoveDirection, self.direction)
            )
