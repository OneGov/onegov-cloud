from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.pas.models import PASChange
from sqlalchemy import desc

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class ChangeCollection(GenericCollection[PASChange]):

    @property
    def model_class(self) -> type[PASChange]:
        return PASChange

    def query(self) -> Query[PASChange]:
        return super().query().order_by(desc(PASChange.last_change))
