from __future__ import annotations

from onegov.core.collection import GenericCollection, Pagination
from onegov.translator_directory.models.time_report import (
    TranslatorTimeReport,
)
from sqlalchemy import desc, extract


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
        month: int | None = None,
        year: int | None = None,
    ) -> None:
        super().__init__(app.session())
        self.app = app
        self.page = page
        self.month = month
        self.year = year

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.month == other.month
            and self.year == other.year
        )

    def query(self) -> Query[TranslatorTimeReport]:
        q = self.session.query(TranslatorTimeReport)
        if self.year is not None:
            q = q.filter(
                extract('year', TranslatorTimeReport.assignment_date)
                == self.year
            )
        if self.month is not None:
            q = q.filter(
                extract('month', TranslatorTimeReport.assignment_date)
                == self.month
            )
        return q.order_by(desc(TranslatorTimeReport.assignment_date))

    @property
    def page_index(self) -> int:
        return self.page

    def subset(self) -> Query[TranslatorTimeReport]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.app, index, self.month, self.year)

    def for_accounting_export(
        self, year: int, month: int
    ) -> Query[TranslatorTimeReport]:
        """Query confirmed time reports for a specific month."""
        return (
            self.query()
            .filter(TranslatorTimeReport.status == 'confirmed')
            .filter(
                extract('year', TranslatorTimeReport.assignment_date) == year
            )
            .filter(
                extract('month', TranslatorTimeReport.assignment_date) == month
            )
        )
