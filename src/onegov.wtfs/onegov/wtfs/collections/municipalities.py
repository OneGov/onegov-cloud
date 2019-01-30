from onegov.core.collection import GenericCollection
from onegov.wtfs.models import Municipality


class MunicipalityCollection(GenericCollection):

    @property
    def model_class(self):
        return Municipality

    def query(self):
        query = super(MunicipalityCollection, self).query()
        query = query.order_by(None).order_by(Municipality.name)
        return query
