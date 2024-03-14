from onegov.core.collection import GenericCollection
from onegov.pas.models import ParliamentarianRole

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class ParliamentarianRoleCollection(GenericCollection[ParliamentarianRole]):

    @property
    def model_class(self) -> type[ParliamentarianRole]:
        return ParliamentarianRole

    def query(self) -> 'Query[ParliamentarianRole]':
        return super().query()
