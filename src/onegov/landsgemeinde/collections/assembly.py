from onegov.core.collection import GenericCollection
from onegov.landsgemeinde.models import Assembly
from sqlalchemy import desc
from sqlalchemy.orm import undefer


class AssemblyCollection(GenericCollection):

    @property
    def model_class(self):
        return Assembly

    def query(self):
        return super().query().order_by(desc(Assembly.date))

    def by_id(self, id):
        return self.query().filter(Assembly.id == id).first()

    def by_date(self, date_):
        query = self.query().filter(Assembly.date == date_)
        query = query.options(undefer(Assembly.content))
        return query.first()
