from __future__ import annotations

from datetime import timedelta
from libres.db.models import Allocation, Reservation
from onegov.core.orm import ModelBase
from onegov.pay import Payable, Price
from onegov.reservation.models.resource import Resource
from sedate import utcnow
from sqlalchemy.orm import object_session


class CustomReservation(Reservation, ModelBase, Payable):
    __mapper_args__ = {'polymorphic_identity': 'custom'}  # type:ignore

    @property
    def resource_obj(self) -> Resource:
        return object_session(self).query(
            Resource).filter_by(id=self.resource).one()

    @property
    def payable_reference(self) -> str:
        return f'{self.resource.hex}/{self.email}x{self.quota}'

    @property
    def is_adjustable(self) -> bool:
        """ Returns whether or not the reservation is adjustable.

        A reservation is adjustable when it's not yet been accepted,
        its start date is in the future and its target allocation is
        partly available.

        """
        if self.display_start() < utcnow():
            return False

        if self.data and self.data.get('accepted'):
            return False

        return object_session(self).query(
            self
            ._target_allocations()
            .filter(Allocation.partly_available.is_(True))
            .exists()
        ).scalar()

    def price(self, resource: Resource | None = None) -> Price | None:
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
            assert self.start is not None and self.end is not None
            duration = self.end + timedelta(microseconds=1) - self.start
            hours = duration.total_seconds() / 3600

            assert resource.price_per_hour is not None
            return Price(hours * resource.price_per_hour, resource.currency)

        if resource.pricing_method == 'per_item':
            count = self.quota

            assert resource.price_per_item is not None
            return Price(count * resource.price_per_item, resource.currency)

        raise NotImplementedError
