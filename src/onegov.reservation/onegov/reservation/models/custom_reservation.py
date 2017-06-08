from datetime import timedelta
from libres.db.models import Reservation
from onegov.core.orm import ModelBase
from onegov.form.core import Price
from onegov.pay import Payable
from onegov.reservation.models.resource import Resource
from sqlalchemy.orm import object_session


class CustomReservation(Reservation, ModelBase, Payable):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

    @property
    def resource_obj(self):
        return object_session(self).query(Resource)\
            .filter_by(id=self.resource).one()

    @property
    def price(self):
        """ Returns the price of the reservation.

        Even though one token may point to multiple reservations the price
        is bound to the reservation record.

        The price per token is calculcated by combining all the prices.

        """

        resource = self.resource_obj

        if resource.pricing_method not in ('per_hour', 'per_item'):
            return None

        if resource.pricing_method == 'per_hour':
            hours = 0

            for a in self._target_allocations():
                duration = (a.end + timedelta(microseconds=1) - a.start)
                hours += duration.total_seconds() // 3600

            return Price(hours * resource.price_per_hour, resource.currency)

        if resource.pricing_method == 'per_item':
            count = self._target_allocations().count() * self.quota

            return Price(count * resource.price_per_item, resource.currency)
