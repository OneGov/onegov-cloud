from datetime import timedelta
from libres.db.models import Reservation
from onegov.core.orm import ModelBase
from onegov.pay import Payable, Price
from onegov.reservation.models.resource import Resource
from sqlalchemy.orm import object_session


class CustomReservation(Reservation, ModelBase, Payable):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

    @property
    def resource_obj(self):
        return object_session(self).query(Resource)\
            .filter_by(id=self.resource).one()

    def price(self, resource=None):
        """ Returns the price of the reservation.

        Even though one token may point to multiple reservations the price
        is bound to the reservation record.

        The price per token is calculcated by combining all the prices.

        """

        resource = resource or self.resource_obj

        if resource.pricing_method not in ('per_hour', 'per_item'):
            return None

        # technically we could have multiple allocations per reservation
        # but in practice we don't use that feature. Each reservation
        # links to exactly one allocation.
        #
        # As a result we can take a substantial shortcut here and calculate
        # the price on the reservation itself instead of loading all
        # allocations.

        if resource.pricing_method == 'per_hour':
            duration = self.end + timedelta(microseconds=1) - self.start
            hours = duration.total_seconds() // 3600

            return Price(hours * resource.price_per_hour, resource.currency)

        if resource.pricing_method == 'per_item':
            count = self.quota

            return Price(count * resource.price_per_item, resource.currency)

        raise NotImplementedError
