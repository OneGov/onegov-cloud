from onegov.core.collection import GenericCollection
from onegov.core.orm.func import unaccent
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import PickupDate


class MunicipalityCollection(GenericCollection):

    @property
    def model_class(self):
        return Municipality

    def query(self):
        query = super(MunicipalityCollection, self).query()
        query = query.order_by(None).order_by(unaccent(Municipality.name))
        return query

    def import_data(self, data):
        for bfs_number, values in data.items():
            query = self.query()
            query = query.filter(Municipality.meta['bfs_number'] == bfs_number)
            municipality = query.first()
            if not municipality:
                continue

            dates = set(values['dates'])
            dates -= {d.date for d in municipality.pickup_dates}
            for date in dates:
                municipality.pickup_dates.append(PickupDate(date=date))
