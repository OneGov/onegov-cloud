from __future__ import annotations

from functools import cached_property
from itertools import groupby

from onegov.file import File, FileCollection
from onegov.form.validators import WhitelistedMimeType
from onegov.translator_directory.models.translator import Translator


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from uuid import UUID


# This can be changed anytime without making further changes
# We assume - like for the Excel - that we will not add other languages in
# the future and do not use translations strings here
DEFAULT_DOCUMENT_CATEGORIES = (
    'Antrag',
    'Diplome und Zertifikate',
    'Abklärungen',
    'Bestätigungen der Koordinationsstelle',
    'Beschwerden',
    'Korrespondenz',
    'Diverses'
)


class TranslatorDocumentCollection(FileCollection[File]):

    supported_content_types = WhitelistedMimeType.whitelist

    def __init__(
        self,
        session: Session,
        translator_id: UUID,
        category: str | None
    ) -> None:
        super().__init__(session, type='*', allow_duplicates=True)

        self.translator_id = translator_id
        self.category = category or DEFAULT_DOCUMENT_CATEGORIES[0]

    @cached_property
    def translator(self) -> Translator | None:
        return self.session.query(Translator).filter_by(
            id=self.translator_id).first()

    @cached_property
    def unique_categories(self) -> list[str]:
        """Returns a list of the defined default categories and the ones in
        the database."""
        q = self.session.query(File.note).filter(File.note.isnot(None))
        from_files = tuple(f.note for f in q.distinct())
        return sorted(set(from_files + DEFAULT_DOCUMENT_CATEGORIES))

    @property
    def files_by_category(self) -> tuple[tuple[str, tuple[File, ...]], ...]:
        assert self.translator is not None
        files = sorted(self.translator.files, key=lambda f: f.note or '')
        return tuple(
            (category, tuple(files))
            for category, files in groupby(files, key=lambda f: f.note)
        ) if files else ()
