from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.pas.models import Change
from sqlalchemy import desc

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class ChangeCollection(GenericCollection[Change]):

    @property
    def model_class(self) -> type[Change]:
        return Change

    def query(self) -> Query[Change]:
        return super().query().order_by(desc(Change.last_change))
