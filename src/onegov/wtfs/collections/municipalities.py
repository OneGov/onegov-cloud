from onegov.core.collection import GenericCollection
from onegov.core.orm.func import unaccent
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import PickupDate
from sqlalchemy import Integer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class MunicipalityCollection(GenericCollection[Municipality]):

    @property
    def model_class(self) -> type[Municipality]:
        return Municipality

    def query(self) -> 'Query[Municipality]':
        query = super().query()
        query = query.order_by(None).order_by(unaccent(Municipality.name))
        return query

    def import_data(self, data: dict[int, dict[str, Any]]) -> None:
        for bfs_number, values in data.items():
            query = self.query()
            query = query.filter(
                Municipality.meta['bfs_number'].astext.cast(Integer)
                == bfs_number
            )
            municipality = query.first()
            if not municipality:
                continue

            dates = set(values['dates'])
            dates -= {d.date for d in municipality.pickup_dates}
            for date in dates:
                municipality.pickup_dates.append(PickupDate(date=date))
