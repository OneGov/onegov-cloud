from onegov.core.collection import GenericCollection
from onegov.wtfs.models import ScanJob


class ScanJobCollection(GenericCollection):

    @property
    def model_class(self):
        return ScanJob

    def query(self):
        query = super(ScanJobCollection, self).query()
        query = query.order_by(None).order_by(ScanJob.dispatch_date)
        return query
