from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import JSON
from onegov.swissvotes.models.file import FileSubCollection
from onegov.swissvotes.models.file import TranslatablePageFile
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import object_session


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
    from onegov.core.orm.abstract import MoveDirection
    from onegov.swissvotes.request import SwissvotesRequest
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session


class TranslatablePage(Base, TimestampMixin):
    """ A page containing translatable content. """

    __tablename__ = 'swissvotes_page'

    id: 'Column[str]' = Column(Text, nullable=False, primary_key=True)

    title_translations: 'Column[Mapping[str, str]]' = Column(
        HSTORE,
        nullable=False
    )
    title = translation_hybrid(title_translations)

    content_translations: 'Column[Mapping[str, str]]' = Column(
        HSTORE,
        nullable=False
    )
    content = translation_hybrid(content_translations)

    order: 'Column[int | None]' = Column(Integer, default=2 ** 16)

    meta: 'Column[dict[str, Any]]' = Column(JSON, nullable=False, default=dict)

    show_timeline: dict_property[bool] = meta_property(default=False)

    files = associated(TranslatablePageFile, 'files', 'one-to-many')

    @property
    def siblings(self) -> 'Query[TranslatablePage]':
        query = object_session(self).query(TranslatablePage)
        query = query.order_by(TranslatablePage.order)
        return query

    def get_file(
        self,
        name: str,
        request: 'SwissvotesRequest'
    ) -> TranslatablePageFile | None:

        files_from_name = [f for f in self.files if name in f.filename]
        if not files_from_name:
            return None

        files = [f for f in files_from_name if f.locale == request.locale]
        if files:
            return files[0]

        files = [f for f in files_from_name
                 if f.locale == request.default_locale]
        return files[0] if files else None

    def get_file_by_locale(
        self,
        name: str,
        locale: str
    ) -> TranslatablePageFile | None:

        files = [f for f in self.files
                 if name in f.filename and f.locale == locale]
        return files[0] if files else None

    slider_images = FileSubCollection()


class TranslatablePageMove:
    """ Represents a single move of a page. """

    def __init__(
        self,
        session: 'Session',
        subject_id: str,
        target_id: str,
        direction: 'MoveDirection'
    ) -> None:
        self.session = session
        self.subject_id = subject_id
        self.target_id = target_id
        self.direction = direction

    def execute(self) -> None:
        from onegov.swissvotes.collections import TranslatablePageCollection

        pages = TranslatablePageCollection(self.session)
        subject = pages.by_id(self.subject_id)
        target = pages.by_id(self.target_id)
        if subject and target and subject != target:
            pages.move(
                subject=subject,
                target=target,
                direction=self.direction
            )
