from onegov.core.collection import GenericCollection
from onegov.pas.models import Parliamentarian


class ParliamentarianCollection(GenericCollection):

    @property
    def model_class(self):
        return Parliamentarian

    def query(self):
        return super().query().order_by(Parliamentarian.name)

    def by_id(self, id):
        return self.query().filter(Parliamentarian.id == id).first()
