from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from libres.db.models import Allocation, Reservation
from onegov.core.orm import ModelBase
from onegov.pay import InvoiceItemMeta, Payable, Price
from onegov.reservation.models.resource import Resource
from sedate import utcnow
from sqlalchemy.orm import object_session


class CustomReservation(Reservation, ModelBase, Payable):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

    @property
    def allocation_obj(self) -> Allocation | None:
        # NOTE: The way we use reservations, we should only ever really
        #       target a single master allocation, but we don't really
        #       want to crash if that assumption doesn't hold, if we
        #       somehow target multiple allocations, we use the first
        #       one as a reference for things like pricing.
        return self._target_allocations().first()

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

        return object_session(self).query(
            self
            ._target_allocations()
            .filter(Allocation.partly_available.is_(True))
            .exists()
        ).scalar()

    def invoice_item(
        self,
        resource: Resource | None = None,
        allocation: Allocation | None = None
    ) -> InvoiceItemMeta | None:
        """ Returns an invoice item for this reservation. """

        allocation = allocation or self.allocation_obj
        data = allocation and allocation.data or {}
        pricing_method = data.get('pricing_method', 'inherit')
        if pricing_method not in ('inherit', 'per_hour', 'per_item'):
            return None

        resource = resource or self.resource_obj
        if pricing_method == 'inherit':
            pricing_method = resource.pricing_method

            if pricing_method not in ('per_hour', 'per_item'):
                return None

            price_per_hour = resource.price_per_hour
            price_per_item = resource.price_per_item
        else:
            price_per_hour = data.get('price_per_hour', 0.0)
            price_per_item = data.get('price_per_item', 0.0)

        # technically we could have multiple allocations per reservation
        # but in practice we don't use that feature. Each reservation
        # links to exactly one allocation.
        #
        # As a result we can take a substantial shortcut here and calculate
        # the price on the reservation itself instead of loading all
        # allocations.

        if pricing_method == 'per_hour':
            assert self.start is not None and self.end is not None
            duration = self.end + timedelta(microseconds=1) - self.start
            hours = Decimal(duration.total_seconds()) / Decimal('3600')

            assert price_per_hour is not None
            return InvoiceItemMeta(
                text=resource.title,
                group='reservation',
                cost_object=resource.cost_object,
                extra={'reservation_id': self.id},
                unit=Decimal(price_per_hour),
                quantity=hours,
            )

        if pricing_method == 'per_item':
            count = self.quota

            assert price_per_item is not None
            return InvoiceItemMeta(
                text=resource.title,
                group='reservation',
                cost_object=resource.cost_object,
                extra={'reservation_id': self.id},
                unit=Decimal(price_per_item),
                quantity=Decimal(count),
            )

        raise NotImplementedError

    def price(
        self,
        resource: Resource | None = None,
        allocation: Allocation | None = None,
    ) -> Price | None:
        """ Returns the price of the reservation.

        Even though one token may point to multiple reservations the price
        is bound to the reservation record.

        The price per token is calculcated by combining all the prices.

        """
        resource = resource or self.resource_obj
        allocation = allocation or self.allocation_obj

        item = self.invoice_item(resource, allocation)
        if item is None:
            return None

        data = allocation and allocation.data or {}
        if data.get('pricing_method', 'inherit') == 'inherit':
            currency = resource.currency
        else:
            currency = data.get('currency') or resource.currency
        return Price(item.amount, currency)
