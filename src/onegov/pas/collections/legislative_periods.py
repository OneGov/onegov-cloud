from onegov.core.collection import GenericCollection
from onegov.pas.models import LegislativePeriod


class LegislativePeriodCollection(GenericCollection):

    @property
    def model_class(self):
        return LegislativePeriod

    def query(self):
        return super().query().order_by(LegislativePeriod.name)

    def by_id(self, id):
        return self.query().filter(LegislativePeriod.id == id).first()
