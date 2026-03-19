from __future__ import annotations

from onegov.core.collection import GenericCollection, Pagination
from onegov.translator_directory.models.time_report import (
    TranslatorTimeReport,
)
from onegov.translator_directory.models.translator import Translator
from sqlalchemy import asc


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.translator_directory.app import TranslatorDirectoryApp
    from sqlalchemy.orm import Query
    from typing import Self


class TimeReportCollection(
    GenericCollection[TranslatorTimeReport], Pagination[TranslatorTimeReport]
):

    batch_size = 20

    def __init__(
        self,
        app: TranslatorDirectoryApp,
        page: int = 0,
        archive: bool = False,
    ) -> None:
        super().__init__(app.session())
        self.app = app
        self.page = page
        self.archive = archive

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.archive == other.archive
        )

    def query(self) -> Query[TranslatorTimeReport]:
        q = (
            self.session.query(TranslatorTimeReport)
            .join(Translator)
        )
        if self.archive:
            q = q.filter(TranslatorTimeReport.exported == True)
        else:
            q = q.filter(TranslatorTimeReport.exported == False)
        return q.order_by(
            asc(Translator.pers_id),
            asc(TranslatorTimeReport.created),
        )

    @property
    def page_index(self) -> int:
        return self.page

    def subset(self) -> Query[TranslatorTimeReport]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.app, index, self.archive)

    @property
    def batch(self) -> tuple[TranslatorTimeReport, ...]:
        return tuple(self.transform_batch_query(self.cached_subset))

    def for_accounting_export(self) -> Query[TranslatorTimeReport]:
        """Query confirmed, unexported time reports sorted by pers_id
        and assignment date."""
        return (
            self.session.query(TranslatorTimeReport)
            .join(Translator)
            .filter(TranslatorTimeReport.status == 'confirmed')
            .filter(TranslatorTimeReport.exported == False)
            .order_by(
                asc(Translator.pers_id),
                asc(TranslatorTimeReport.created),
            )
        )
