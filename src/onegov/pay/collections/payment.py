from __future__ import annotations

import sedate

from collections import defaultdict
from functools import cached_property
from onegov.core.collection import GenericCollection, Pagination
from onegov.pay.models import Payment
from onegov.ticket.models.ticket import Ticket
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, func


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable
    from datetime import date, datetime
    from decimal import Decimal
    from onegov.pay.types import AnyPayableBase, PaymentState
    from sedate.types import Direction, TzInfo
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


class PaymentCollection(GenericCollection[Payment], Pagination[Payment]):
    """ Manages the payment records.

    To render a list of payments you might want to also consider the
    :class:`onegov.pay.collection.payable.Paybale` collection, which renders
    payments by loading the linked records first.

    """

    page: int
    batch_size = 50

    def __init__(
        self,
        session: Session,
        source: str = '*',
        page: int = 0,
        start: datetime | None = None,
        end: datetime | None = None,
        ticket_group: str | None = None,
        ticket_start: date | None = None,
        ticket_end: date | None = None,
        reservation_start: date | None = None,
        reservation_end: date | None = None,
        status: str | None = None,
        payment_type: str | None = None
    ):
        GenericCollection.__init__(self, session)
        Pagination.__init__(self, page)
        self.source = source
        self.start = start
        self.end = end
        self.status = status
        self.payment_type = payment_type
        self.ticket_group = ticket_group
        self.ticket_start = ticket_start
        self.ticket_end = ticket_end
        self.reservation_start = reservation_start
        self.reservation_end = reservation_end

    @property
    def model_class(self) -> type[Payment]:
        return Payment.get_polymorphic_class(self.source, Payment)

    def add(
        self,
        *,
        source: str | None = None,
        amount: Decimal | None = None,
        currency: str = 'CHF',
        remote_id: str | None = None,
        state: PaymentState = 'open',
        # FIXME: We probably don't want to allow arbitrary kwargs
        #        but we need to make sure, we don't use any other
        #        ones somewhere first
        **kwargs: Any
    ) -> Payment:

        if source is None:
            if self.source == '*':
                source = 'generic'
            else:
                source = self.source

        return super().add(
            source=source,
            amount=amount,
            currency=currency,
            remote_id=remote_id,
            state=state,
            **kwargs
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PaymentCollection):
            return False

        return (
            self.source == other.source
            and self.page == other.page
            and self.start == other.start
            and self.end == other.end
            and self.ticket_group == other.ticket_group
            and self.ticket_start == other.ticket_start
            and self.ticket_end == other.ticket_end
            and self.reservation_start == other.reservation_start
            and self.reservation_end == other.reservation_end
            and self.status == other.status
            and self.payment_type == other.payment_type
        )

    @cached_property
    def tzinfo(self) -> TzInfo:
        return sedate.ensure_timezone('Europe/Zurich')

    def align_date(self, value: date, direction: Direction) -> datetime:
        return sedate.align_date_to_day(
            sedate.replace_timezone(sedate.as_datetime(value), self.tzinfo),
            self.tzinfo,
            direction
        )

    def subset(self) -> Query[Payment]:
        query = self.query()

        if self.start:
            query = query.filter(Payment.created >= self.start)

        if self.end:
            query = query.filter(Payment.created <= self.end)

        # Filter by payment type
        if self.payment_type == 'manual':
            query = query.filter(Payment.provider_id.is_(None))
        elif self.payment_type == 'provider':
            query = query.filter(Payment.provider_id.isnot(None))

        # Filter by payment status
        if self.status:
            query = query.filter(Payment.state == self.status)

        # Filter payments by each associated ticket creation date
        if self.ticket_start or self.ticket_end or self.ticket_group:
            query = query.join(Ticket, Payment.id == Ticket.payment_id)
            if self.ticket_group:
                handler_code, *remainder = self.ticket_group.split('-', 1)
                query = query.filter(Ticket.handler_code == handler_code)
                if remainder:
                    group, = remainder
                    query = query.filter(Ticket.group == group)
            if self.ticket_start:
                query = query.filter(Ticket.created >= self.align_date(
                    self.ticket_start,
                    'down'
                ))
            if self.ticket_end:
                query = query.filter(Ticket.created <= self.align_date(
                    self.ticket_end,
                    'up'
                ))

        # Filter payments by the reservation dates it belongs to
        if self.reservation_start or self.reservation_end:
            from onegov.reservation import Reservation

            conditions = []
            if self.reservation_start:
                conditions.append(Reservation.end >= self.align_date(
                    self.reservation_start,
                    'down'
                ))
            if self.reservation_end:
                conditions.append(Reservation.start <= self.align_date(
                    self.reservation_end,
                    'up'
                ))
            query = query.filter(
                Payment.linked_reservations.any(and_(*conditions))  # type: ignore[attr-defined]
            )

        return query.order_by(Payment.created.desc())

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> PaymentCollection:
        return self.__class__(
            self.session,
            page=index,
            start=self.start,
            end=self.end,
            ticket_group=self.ticket_group,
            ticket_start=self.ticket_start,
            ticket_end=self.ticket_end,
            reservation_start=self.reservation_start,
            reservation_end=self.reservation_end,
            payment_type=self.payment_type,
            source=self.source,
            status=self.status
        )

    def tickets_by_batch(self) -> dict[UUID, Ticket]:
        if not self.batch:
            return {}
        session = self.session
        return {ticket.payment_id: ticket  # type: ignore[misc]
            for ticket in session.query(Ticket).filter(
            Ticket.payment_id.in_([el.id for el in self.batch]))
        }

    def reservation_dates_by_batch(self) -> dict[UUID, tuple[date, date]]:
        if not self.batch:
            return {}
        from onegov.reservation import Reservation
        session = self.session
        return {
            payment_id: (
                sedate.to_timezone(start_date, self.tzinfo).date(),
                sedate.to_timezone(end_date, self.tzinfo).date()
            )
            for payment_id, start_date, end_date in session.query(Reservation)
            .join(Reservation.payment)
            .filter(Payment.id.in_([el.id for el in self.batch]))
            .group_by(Payment.id)
            .with_entities(
                Payment.id,
                func.min(Reservation.start),
                func.max(Reservation.end)
            )
        }

    def payment_links_for(
        self,
        items: Collection[Payment]
    ) -> dict[UUID, list[AnyPayableBase]]:
        """ A more efficient way of loading all links of the given batch
        (compared to loading payment.links one by one).

        """
        payment_links = defaultdict(list)

        assert Payment.registered_links is not None
        for link in Payment.registered_links.values():
            targets = self.session.query(
                getattr(link.table.columns, link.key)
            ).filter(
                link.table.columns.payment_id.in_(tuple(
                    p.id for p in items
                ))
            )

            q: Query[AnyPayableBase]
            q = self.session.query(link.cls)
            q = q.filter(link.cls.id.in_(targets.subquery()))  # type:ignore
            q = q.options(joinedload(link.class_attribute))

            for record in q:
                payments = getattr(record, link.attribute)

                try:
                    for payment in payments:
                        payment_links[payment.id].append(record)
                except TypeError:
                    payment_links[payments.id].append(record)

        return payment_links

    def payment_links_by_subset(
        self,
        subset: Iterable[Payment] | None = None
    ) -> dict[UUID, list[AnyPayableBase]]:
        subset_iterable = subset or self.subset()
        return self.payment_links_for(list(subset_iterable))

    def payment_links_by_batch(
        self,
        batch: Collection[Payment] | None = None
    ) -> dict[UUID, list[AnyPayableBase]] | None:
        batch = batch or self.batch

        if not batch:
            return None

        return self.payment_links_for(batch)

    def by_state(self, state: PaymentState) -> PaymentCollection:
        """ Returns a new collection that only contains payments with the
        given state. Resets all other filters.
        """
        return self.__class__(
            self.session,
            page=0,
            start=None,
            end=None,
            ticket_start=None,
            ticket_end=None,
            source=self.source,
            status=state)
