from onegov.core.collection import GenericCollection
from onegov.pas.models import ParliamentarianRole


class ParliamentarianRoleCollection(GenericCollection[ParliamentarianRole]):

    @property
    def model_class(self) -> type[ParliamentarianRole]:
        return ParliamentarianRole
