from onegov.core.collection import GenericCollection
from onegov.landsgemeinde.models import Assembly
from sqlalchemy import desc


class AssemblyCollection(GenericCollection):

    @property
    def model_class(self):
        return Assembly

    def query(self):
        return super().query().order_by(desc(Assembly.date))

    def by_id(self, id):
        return self.query().filter(Assembly.id == id).first()

    def by_date(self, date_):
        return self.query().filter(Assembly.date == date_).first()
