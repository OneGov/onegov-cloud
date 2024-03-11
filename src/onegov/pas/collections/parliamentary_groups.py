from onegov.core.collection import GenericCollection
from onegov.pas.models import ParliamentaryGroup


class ParliamentaryGroupCollection(GenericCollection):

    @property
    def model_class(self):
        return ParliamentaryGroup

    def query(self):
        return super().query().order_by(ParliamentaryGroup.name)

    def by_id(self, id):
        return self.query().filter(ParliamentaryGroup.id == id).first()
