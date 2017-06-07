from datetime import timedelta
from libres.db.models import Allocation
from onegov.core.orm import ModelBase
from onegov.core.orm.mixins import data_property
from onegov.form.core import Price


class PricedAllocation(Allocation, ModelBase):
    __mapper_args__ = {'polymorphic_identity': 'priced'}

    currency = data_property('currency')
    pricing_method = data_property('pricing_method')
    price_per_hour = data_property('price_per_hour')
    price_per_reservation = data_property('price_per_reservation')

    def price(self, quota):
        """ Returns the price of the allocation with the given quota. """

        price = self.unit_price

        if price is not None:
            return Price(price.amount * quota, price.currency)

    @property
    def unit_price(self):
        """ Returns the price of a single allocation. """

        if self.pricing_method is None:
            return None

        if self.pricing_method == 'per_hour':
            duration = (self.end - self.start) + timedelta(microseconds=1)
            hours = (duration.total_seconds() // 3600)
            return Price(hours * self.price_per_hour, self.currency)

        if self.pricing_method == 'per_reservation':
            return Price(self.price_per_reservation, self.currency)

        raise NotImplementedError
