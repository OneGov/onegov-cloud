from cached_property import cached_property
from onegov.core.collection import GenericCollection
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum


class VotumCollection(GenericCollection):

    def __init__(self, session, date=None, agenda_item_number=None):
        self.session = session
        self.date = date
        self.agenda_item_number = agenda_item_number

    @property
    def model_class(self):
        return Votum

    def query(self):
        query = super().query()
        if self.agenda_item:
            query = query.filter(Votum.agenda_item_id == self.agenda_item.id)
        query = query.order_by(Votum.number)
        return query

    def by_id(self, id):
        return self.query().filter(Votum.id == id).first()

    def by_number(self, number):
        return self.query().filter(Votum.number == number).first()

    @cached_property
    def assembly(self):
        if self.date is not None:
            query = self.session.query(Assembly)
            query = query.filter(Assembly.date == self.date)
            return query.first()

    @cached_property
    def agenda_item(self):
        if self.assembly is not None and self.agenda_item_number is not None:
            query = self.session.query(AgendaItem)
            query = query.filter(AgendaItem.assembly_id == self.assembly.id)
            query = query.filter(AgendaItem.number == self.agenda_item_number)
            return query.first()
