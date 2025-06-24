from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models.political_business import PoliticalBusiness

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session


class PoliticalBusinessCollection(GenericCollection[PoliticalBusiness]):

    def __init__(self, session: Session):
        super().__init__(session)

    @property
    def model_class(self) -> type[PoliticalBusiness]:
        return PoliticalBusiness

    def query(self) -> Query[PoliticalBusiness]:
        query = super().query()
        # Assuming PoliticalBusiness has a 'title' attribute for default ordering
        return query.order_by(self.model_class.title)
