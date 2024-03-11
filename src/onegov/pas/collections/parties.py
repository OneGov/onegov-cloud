from onegov.core.collection import GenericCollection
from onegov.pas.models import Party


class PartyCollection(GenericCollection):

    @property
    def model_class(self):
        return Party

    def query(self):
        return super().query().order_by(Party.name)

    def by_id(self, id):
        return self.query().filter(Party.id == id).first()
