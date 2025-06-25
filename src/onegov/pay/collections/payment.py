from __future__ import annotations

from collections import defaultdict

from libres.db.models import Reservation
from onegov.core.collection import GenericCollection, Pagination
from onegov.pay.models import Payment
from sqlalchemy.orm import joinedload
from onegov.core.orm.types import UUID as onegovUUID
from sqlalchemy.sql.expression import cast


from typing import Any, TYPE_CHECKING
from onegov.ticket.model import Ticket
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable
    from datetime import datetime
    from decimal import Decimal
    from onegov.pay.types import AnyPayableBase, PaymentState
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


class PaymentCollection(GenericCollection[Payment], Pagination[Payment]):
    """ Manages the payment records.

    To render a list of payments you might want to also consider the
    :class:`onegov.pay.collection.payable.Paybale` collection, which renders
    payments by loading the linked records first.

    """

    page: int

    def __init__(
        self,
        session: Session,
        source: str = '*',
        page: int = 0,
        start: datetime | None = None,
        end: datetime | None = None,
        ticket_start: datetime | None = None,
        ticket_end: datetime | None =None,
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
        self.ticket_start = ticket_start
        self.ticket_end = ticket_end

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
            and self.status == other.status
            and self.payment_type == other.payment_type
        )

    def subset(self) -> Query[Payment]:
        query = self.query()

        # Filter by payment type
        if self.payment_type == 'manual':
            query = query.filter(Payment.provider_id.is_(None))
        elif self.payment_type == 'provider':
            query = query.filter(Payment.provider_id.isnot(None))

        # Filter by payment status
        if self.status:
            query = query.filter(Payment.state == self.status)

        # Filter by ticket creation date - this is the complex part
        if self.ticket_start or self.ticket_end:
            # Join through reservations to tickets
            breakpoint()
            query = query.join(
                Reservation,
                Payment.id == Reservation.payment_id
            ).join(
                Ticket,
                cast(Reservation.token, onegovUUID) == Ticket.handler_id
            )

            if self.ticket_start:
                query = query.filter(Ticket.created >= self.ticket_start)
            if self.ticket_end:
                query = query.filter(Ticket.created <= self.ticket_end)

        return query.order_by(Payment.created.desc())

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session,
            page=index,
            start=self.start,
            end=self.end,
            ticket_start=self.ticket_start,
            ticket_end=self.ticket_end,
            payment_type=self.payment_type,
            source=self.source,
            status=self.status
        )

    def payment_links_for(
        self,
        items: Iterable[Payment]
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
        subset = subset or self.subset()
        return self.payment_links_for(subset)

    def payment_links_by_batch(
        self,
        batch: Collection[Payment] | None = None
    ) -> dict[UUID, list[AnyPayableBase]] | None:
        batch = batch or self.batch

        if not batch:
            return None

        return self.payment_links_for(batch)
