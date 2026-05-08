from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.core.collection import Pagination
from onegov.pas.models import Change
from sqlalchemy import desc

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class ChangeCollection(GenericCollection[Change], Pagination[Change]):

    batch_size = 20

    def __init__(self, session: Session, page: int = 0):
        GenericCollection.__init__(self, session)
        Pagination.__init__(self, page)

    @property
    def model_class(self) -> type[Change]:
        return Change

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ChangeCollection) and self.page == other.page

    def subset(self) -> Query[Change]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, index)

    def query(self) -> Query[Change]:
        return super().query().order_by(desc(Change.last_change))
