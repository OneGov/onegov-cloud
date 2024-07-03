from collections import defaultdict
from onegov.core.collection import GenericCollection, Pagination
from onegov.pay.models import Payment
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import undefer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable
    from datetime import datetime
    from decimal import Decimal
    from onegov.pay.types import AnyPayableBase, PaymentState
    from sqlalchemy.orm import Query, Session
    from typing_extensions import Self
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
        session: 'Session',
        source: str = '*',
        page: int = 0,
        start: 'datetime | None' = None,
        end: 'datetime | None' = None
    ):
        GenericCollection.__init__(self, session)
        Pagination.__init__(self, page)
        self.source = source
        self.start = start
        self.end = end

    @property
    def model_class(self) -> type[Payment]:
        return Payment.get_polymorphic_class(self.source, Payment)

    def add(
        self,
        *,
        source: str | None = None,
        amount: 'Decimal | None' = None,
        currency: str = 'CHF',
        remote_id: str | None = None,
        state: 'PaymentState' = 'open',
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
        )

    def subset(self) -> 'Query[Payment]':
        q = self.query().order_by(desc(Payment.created))

        if self.start:
            q = q.filter(self.start <= Payment.created)

        if self.end:
            q = q.filter(Payment.created <= self.end)

        q = q.options(joinedload(Payment.provider))  # type:ignore[misc]
        q = q.options(undefer(Payment.created))
        return q

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> 'Self':
        return self.__class__(self.session, self.source, index)

    def payment_links_for(
        self,
        items: 'Iterable[Payment]'
    ) -> dict['UUID', list['AnyPayableBase']]:
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
        subset: 'Iterable[Payment] | None' = None
    ) -> dict['UUID', list['AnyPayableBase']]:
        subset = subset or self.subset()
        return self.payment_links_for(subset)

    def payment_links_by_batch(
        self,
        batch: 'Collection[Payment] | None' = None
    ) -> dict['UUID', list['AnyPayableBase']] | None:
        batch = batch or self.batch

        if not batch:
            return None

        return self.payment_links_for(batch)
