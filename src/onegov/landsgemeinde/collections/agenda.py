from onegov.core.collection import GenericCollection
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly


class AgendaItemCollection(GenericCollection):

    def __init__(self, session, assembly_id=None):
        self.session = session
        self.assembly_id = assembly_id

    @property
    def model_class(self):
        return AgendaItem

    def query(self):
        query = super().query()
        if self.assembly_id is not None:
            query = query.filter(AgendaItem.assembly_id == self.assembly_id)
        query = query.order_by(AgendaItem.number)
        return query

    def by_id(self, id):
        return self.query().filter(AgendaItem.id == id).first()

    @property
    def assembly(self):
        if self.assembly_id is not None:
            query = self.session.query(Assembly)
            query = query.filter(Assembly.id == self.assembly_id)
            return query.one()
