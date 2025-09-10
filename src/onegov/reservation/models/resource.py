from __future__ import annotations

import datetime
import secrets

from decimal import Decimal
from dataclasses import replace
from functools import lru_cache
from libres import new_scheduler
from libres.db.models import Allocation
from libres.db.models.base import ORMBase
from onegov.core.orm import ModelBase
from onegov.core.orm.mixins import (
    content_property, dict_property, meta_property)
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from onegov.file import MultiAssociatedFiles
from onegov.form import parse_form
from onegov.pay import InvoiceItemMeta, Price, process_payment
from sedate import align_date_to_day, utcnow
from sqlalchemy import Column, Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    # type gets shadowed by type in model, so we use Type as an alias
    from builtins import type as type_t
    from collections.abc import Sequence
    from libres.context.core import Context
    from libres.db.scheduler import Scheduler
    from onegov.form import Form
    from onegov.reservation.models import CustomReservation
    from onegov.pay import (
        InvoiceDiscountMeta, Payment, PaymentError, PaymentProvider)
    from onegov.pay.types import PaymentMethod
    from typing import TypeAlias

    DeadlineUnit: TypeAlias = Literal['d', 'h']

    # HACK: We pass a UUID as a name and have a custom uuid_generator
    #       which directly uses it, so in order to get the correct
    #       type checking on Scheduler.name, we have to pretend we
    #       created a subclass
    class _OurScheduler(Scheduler):
        name: uuid.UUID  # type:ignore[assignment]


@lru_cache(maxsize=1)
def extra_scheduler_arguments() -> dict[str, Any]:
    from onegov.reservation.models import CustomReservation
    from onegov.reservation.models import CustomAllocation

    return {
        'allocation_cls': CustomAllocation,
        'reservation_cls': CustomReservation
    }


class Resource(ORMBase, ModelBase, ContentMixin,
               TimestampMixin, MultiAssociatedFiles):
    """ A resource holds a single calendar with allocations and reservations.

    Note that this resource is not defined on the onegov.core declarative base.
    Instead it is defined using the libres base. This means we can't join
    data outside the libres models.

    This should however not be a problem as this onegov module is self
    contained and does not link to other onegov modules, except for core.

    If we ever want to link to other models (say link a reservation to a user),
    then we have to switch to a unified base. Ideally we would find a way
    to merge these bases somehow.

    Also note that we *do* use the ModelBase class as a mixin to at least share
    the same methods as all the usual onegov.core.orm models.

    """

    __tablename__ = 'resources'

    #: the unique id
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: a nice id for the url, readable by humans
    # FIXME: This probably should've been nullable=False
    name: Column[str | None] = Column(Text, primary_key=False, unique=True)

    #: the title of the resource
    title: Column[str] = Column(Text, primary_key=False, nullable=False)

    #: the timezone this resource resides in
    timezone: Column[str] = Column(Text, nullable=False)

    #: the custom form definition used when creating a reservation
    definition: Column[str | None] = Column(Text, nullable=True)

    #: the group to which this resource belongs to (may be any kind of string)
    group: Column[str | None] = Column(Text, nullable=True)

    #: the subgroup to which this resource belongs to
    subgroup: Column[str | None] = Column(Text, nullable=True)

    #: the type of the resource, this can be used to create custom polymorphic
    #: subclasses. See `<https://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    #: the payment method
    payment_method: dict_property[PaymentMethod | None] = content_property()

    #: the minimum price total the reservation must exceed
    minimum_price_total: dict_property[float | None] = content_property()

    #: the currency of the price to pay
    currency: dict_property[str | None] = content_property()

    #: the pricing method to use
    pricing_method: dict_property[str | None] = content_property()

    #: the reservations cost a given amount per hour
    price_per_hour: dict_property[float | None] = content_property()

    #: the reservations cost a given amount per unit (allocations * quota)
    price_per_item: dict_property[float | None]
    price_per_item = content_property('price_per_reservation')

    #: extra field values to include in the ical event description
    ical_fields: dict_property[list[str]] = content_property(default=list)

    #: reservation deadline (e.g. None, (5, 'd'), (24, 'h'))
    deadline: dict_property[tuple[int, DeadlineUnit] | None]
    deadline = content_property()

    #: the pricing method to use for extras defined in formcode
    extras_pricing_method: dict_property[str | None] = content_property()

    #: the default view
    default_view: dict_property[str | None] = content_property()

    #: reservation zip code limit, contains None or something like this:
    #: {
    #:     'zipcode_field': 'PLZ',
    #:     'zipcode_list': [1234, 5678],
    #:     'zipcode_days': 3
    #: }
    #:
    #: zipcode_field -> the field name in the definition containing zip codes
    #: zipcode_list -> zip codes exempt from the rule
    #: zipcode_days -> how many days before the reservation the rule is dropped
    #:
    #: Note, the zipcode_field name is in the human readable form.
    # FIXME: Define a TypedDict with all the zipcode_block elements
    zipcode_block: dict_property[dict[str, Any] | None] = content_property()

    #: secret token to get anonymous access to calendar data
    access_token: dict_property[str | None] = content_property()

    #: hint on how to get to the resource
    pick_up: dict_property[str | None] = content_property()

    #: the reply_to address to supersede the global reply_to address for
    #: tickets created through this form
    reply_to: dict_property[str | None] = meta_property()

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic'
    }

    allocations: relationship[list[Allocation]] = relationship(
        Allocation,
        cascade='all, delete-orphan',
        primaryjoin='Resource.id == Allocation.resource',
        foreign_keys='Allocation.resource'
    )

    #: the date to jump to in the view (if not None) -> not in the db!
    date: datetime.date | None = None

    #: a range of allocation ids to highlight in the view (if not None)
    highlights_min: int | None = None
    highlights_max: int | None = None

    #: the view to open in the calendar (fullCalendar view name)
    view: str | None = 'dayGridMonth'

    @deadline.setter
    def set_deadline(self, value: tuple[int, DeadlineUnit] | None) -> None:
        value = value or None

        if value:
            if len(value) != 2:
                raise ValueError('Deadline is not a tuple with two elements')

            if not isinstance(value[0], int):
                raise ValueError('Deadline value is not an int')

            if value[0] < 1:
                raise ValueError('Deadline value is smaller than 1')

            if value[1] not in ('d', 'h'):
                raise ValueError("Deadline unit must be 'd' or 'h'")

        self.content['deadline'] = value

    def highlight_allocations(
        self,
        allocations: Sequence[Allocation]
    ) -> None:
        """ The allocation to jump to in the view. """

        # we can assume that allocation ids are created in a continuous
        # number line. It's not necessarily guaranteed, but since it *is*
        # only a highlighting feature we can check the highlights more
        # effiecently if we follow this assumption.
        highlights = [a.id for a in allocations]

        self.highlights_min = min(highlights)
        self.highlights_max = max(highlights)

        self.date = allocations[0].start.date()

    def get_scheduler(self, libres_context: Context) -> _OurScheduler:
        assert self.id, 'the id needs to be set'
        assert self.timezone, 'the timezone needs to be set'

        # HACK: we work around the name being a str in libres, but a
        #       UUID in onegov
        return new_scheduler(  # type:ignore[return-value]
            libres_context,
            self.id,  # type:ignore[arg-type]
            self.timezone,
            **extra_scheduler_arguments()
        )

    @property
    def scheduler(self) -> _OurScheduler:
        assert hasattr(self, 'libres_context'), 'not bound to libres context'
        return self.get_scheduler(self.libres_context)

    def bind_to_libres_context(self, libres_context: Context) -> None:
        self.libres_context = libres_context

    @property
    def form_class(self) -> type_t[Form] | None:
        """ Parses the form definition and returns a form class. """

        if not self.definition:
            return None

        return parse_form(self.definition)

    def invoice_items_for_reservation(
        self,
        reservations: Sequence[CustomReservation],
        extras: Sequence[InvoiceItemMeta] | None = None,
        discounts: Sequence[InvoiceDiscountMeta] | None = None,
        *,
        # HACK: This isn't great, but similarly adding i18n to
        #       the reservation module for a single translation
        #       string is similarly not great. For now we'll
        #       live with this, even if it's ugly.
        reduced_amount_label: str,
    ) -> list[InvoiceItemMeta]:

        if not reservations:
            return []

        items: list[InvoiceItemMeta] = []
        extras_quantity = Decimal('0')
        for reservation in reservations:
            item = reservation.invoice_item(self)
            if item is not None:
                items.append(item)

            if extras:
                match self.extras_pricing_method:
                    case 'one_off':
                        extras_quantity = Decimal('1')

                    case 'per_hour':
                        # FIXME: Should we assert here or instead use
                        #        reservation.timespans()? We assert in
                        #        CustomReservation.price().
                        if reservation.start and reservation.end:
                            duration = reservation.end - reservation.start
                            # compensate for the end being offset
                            duration += datetime.timedelta(microseconds=1)
                        else:
                            duration = datetime.timedelta(seconds=0)

                        extras_quantity += (
                            Decimal(duration.total_seconds())
                            / Decimal('3600')
                        )

                    case 'per_item' | None:
                        extras_quantity += Decimal(reservation.quota)

                    case _:  # pragma: unreachable
                        raise ValueError('unhandled extras pricing method')

        extras = [
            replace(extra, quantity=extras_quantity)
            for extra in (extras or ())
        ]
        total = InvoiceItemMeta.total(items)
        extras_total = InvoiceItemMeta.total(extras)

        # TODO: Currently discounts only apply to the total before
        #       the extras are applied, in the future we may have
        #       discounts that only apply to the extras or both
        discount_items: list[InvoiceItemMeta] = []
        if discounts:
            remainder = total
            for discount in discounts:
                item = discount.apply_discount(total, remainder)
                remainder += item.amount
                assert remainder >= Decimal('0')
                discount_items.append(item)
            total = remainder

        if extras_total and total:
            total += extras_total
        elif extras_total:
            total = extras_total

        items = items + discount_items + extras

        reservation = reservations[0]
        meta = (reservation.data or {}).get('ticket_tag_meta', {})
        # HACK: This is not very robust, we should probably come up
        #       with something better to handle price reductions for
        #       specific tags
        try:
            reduced_amount = Decimal(meta.get('Price', meta.get('Preis')))
            assert reduced_amount >= Decimal('0')
        except Exception:
            reduced_amount = None

        if reduced_amount is not None and reduced_amount < total:
            items.append(InvoiceItemMeta(
                text=reduced_amount_label,
                group='reduced_amount',
                unit=reduced_amount-total
            ))

        return items

    def process_payment(
        self,
        price: Price | None,
        provider: PaymentProvider[Any] | None = None,
        payment_token: str | None = None
    ) -> Payment | PaymentError | Literal[True] | None:
        """ Processes the payment for the given reservation token. """

        if price and price.amount > 0:
            assert self.payment_method is not None
            return process_payment(
                self.payment_method, price, provider, payment_token)

        # FIXME: Returning a boolean is a bit strange here, do we
        #        make use of it or can we change this to None?
        return True

    def is_past_deadline(self, dt: datetime.datetime) -> bool:
        if not self.deadline:
            return False

        if not dt.tzinfo:
            raise RuntimeError(f'The given date has no timezone: {dt}')

        if not self.timezone:
            raise RuntimeError('No timezone set on the resource')

        n, unit = self.deadline

        match unit:
            case 'h':
                # hours result in a simple offset
                deadline = dt - datetime.timedelta(hours=n)

            case 'd':
                # days require that we align the date
                # to the beginning of the date
                deadline = (
                    align_date_to_day(dt, self.timezone, 'down')
                    - datetime.timedelta(days=(n - 1))
                )

            case _:  # pragma: unreachable
                raise AssertionError('unreachable')

        return deadline <= utcnow()

    def is_zip_blocked(self, date: datetime.date) -> bool:
        if not self.zipcode_block:
            return False

        today = datetime.date.today()
        return (date - today).days > self.zipcode_block['zipcode_days']

    def is_allowed_zip_code(self, zipcode: int) -> bool:
        assert isinstance(zipcode, int)

        if not self.zipcode_block:
            return True

        return zipcode in self.zipcode_block['zipcode_list']

    def renew_access_token(self) -> None:
        self.access_token = secrets.token_hex(16)

    def __repr__(self) -> str:
        return f'{self.title}, {self.group}'
