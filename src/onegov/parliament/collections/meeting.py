from __future__ import annotations

from datetime import date
from onegov.core.collection import GenericCollection
from sqlalchemy import or_

from typing import TYPE_CHECKING

from onegov.parliament.models import Meeting

if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class MeetingCollection(GenericCollection[Meeting]):

    @property
    def model_class(self) -> type[Meeting]:
        return Meeting

    def query(self) -> Query[Meeting]:
        query = super().query()
        return query.order_by(self.model_class.start_datetime.desc())

