from cached_property import cached_property
from onegov.core.collection import GenericCollection
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly


class AgendaItemCollection(GenericCollection):

    def __init__(self, session, date=None):
        self.session = session
        self.date = date

    @property
    def model_class(self):
        return AgendaItem

    def query(self):
        query = super().query()
        if self.assembly:
            query = query.filter(AgendaItem.assembly_id == self.assembly.id)
        query = query.order_by(AgendaItem.number)
        return query

    def by_id(self, id):
        return self.query().filter(AgendaItem.id == id).first()

    def by_number(self, number):
        return self.query().filter(AgendaItem.number == number).first()

    @cached_property
    def assembly(self):
        if self.date is not None:
            query = self.session.query(Assembly)
            query = query.filter(Assembly.date == self.date)
            return query.first()
