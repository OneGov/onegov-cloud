from __future__ import annotations

import sedate

from datetime import datetime
from onegov.core.collection import GenericCollection
from onegov.file import File
from sqlalchemy import and_, text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sedate.types import TzInfoOrName
    from sqlalchemy.orm import Query, Session
    from typing import Self


class PublicationCollection(GenericCollection[File]):

    def __init__(self, session: Session, year: int | None = None) -> None:
        super().__init__(session)
        self.year = year

    @property
    def model_class(self) -> type[File]:
        return File

    def query(self) -> Query[File]:
        query = super().query().filter(
            self.model_class.published.is_(True),
            self.model_class.publication.is_(True),
            text("reference->>'content_type' = :content_type").bindparams(
                content_type='application/pdf'
            )
        )

        if self.year:
            s = sedate.replace_timezone(datetime(self.year, 1, 1), 'UTC')
            e = sedate.replace_timezone(datetime(self.year + 1, 1, 1), 'UTC')

            query = query.filter(and_(s <= File.created, File.created < e))

        return query

    def for_year(self, year: int | None) -> Self:
        return self.__class__(self.session, year)

    def first_year(self, timezone: TzInfoOrName) -> int | None:
        query = (
            self.for_year(None).query()
            .with_entities(File.created)
            .order_by(File.created)
        )

        first_record = query.first()

        if first_record:
            return sedate.to_timezone(first_record.created, timezone).year
        return None
