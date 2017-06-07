from libres.db.models import Reservation
from onegov.core.orm import ModelBase
from onegov.form.core import Price
from onegov.pay import Payable


class PayableReservation(Reservation, ModelBase, Payable):
    __mapper_args__ = {'polymorphic_identity': 'payable'}

    @property
    def price(self):
        """ Returns the price of the reservation.

        Even though one token may point to multiple reservations the price
        is bound to the reservation record.

        The price per token is calculcated by combining all the prices.

        """

        prices = []

        for allocation in self._target_allocations():
            prices.append(allocation.price(self.quota))

        amounts = tuple(p.amount for p in prices if p)

        if not amounts:
            return None

        currencies = {p.currency for p in prices if p}
        assert len(currencies) == 1

        return Price(sum(amounts), tuple(currencies)[0])
