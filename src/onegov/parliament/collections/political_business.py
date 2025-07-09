from __future__ import annotations

from onegov.core.collection import GenericCollection, Pagination
from onegov.parliament.models.political_business import PoliticalBusiness

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session


class PoliticalBusinessCollection(
    GenericCollection[PoliticalBusiness],
    Pagination[PoliticalBusiness]
):

    def __init__(
        self,
        session: Session,
        page: int = 0
    ) -> None:
        super().__init__(session)
        self.page = page
        self.batch_size = 20

    @property
    def model_class(self) -> type[PoliticalBusiness]:
        return PoliticalBusiness

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
        )

    def query(self) -> Query[PoliticalBusiness]:
        query = super().query()
        return query.order_by(self.model_class.entry_date.desc())

    def subset(self) -> Query[PoliticalBusiness]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index)

    @property
    def page_index(self) -> int:
        return self.page
