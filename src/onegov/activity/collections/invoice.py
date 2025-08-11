from __future__ import annotations

from functools import cached_property
from onegov.activity.models import BookingPeriodInvoice, ActivityInvoiceItem
from onegov.pay.collections import InvoiceCollection
from onegov.pay.models.invoice_reference import KNOWN_SCHEMAS, Schema
from sqlalchemy import func
from onegov.user import User
from uuid import uuid4, UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from sqlalchemy.orm import Query, Session
    from typing import Self


class BookingPeriodInvoiceCollection(
    InvoiceCollection[BookingPeriodInvoice, ActivityInvoiceItem]
):

    def __init__(
        self,
        session: Session,
        period_id: UUID | None = None,
        user_id: UUID | None = None,
        schema: str = 'feriennet-v1',
        schema_config: dict[str, Any] | None = None
    ) -> None:

        super().__init__(session, type='booking_period', item_type='activity')
        self.user_id = user_id
        self.period_id = period_id

        if schema not in KNOWN_SCHEMAS:
            raise RuntimeError(f'Unknown schema: {schema}')

        self.schema_name = schema
        self.schema_config = (schema_config or {})

    @property
    def model_class(self) -> type[BookingPeriodInvoice]:
        return BookingPeriodInvoice

    @property
    def item_model_class(self) -> type[ActivityInvoiceItem]:
        return ActivityInvoiceItem

    @cached_property
    def schema(self) -> Schema:
        return KNOWN_SCHEMAS[self.schema_name](**self.schema_config)

    def query(
        self,
        ignore_period_id: bool = False
    ) -> Query[BookingPeriodInvoice]:
        q = super().query()

        if self.user_id:
            q = q.filter_by(user_id=self.user_id)

        if self.period_id is not None and not ignore_period_id:
            q = q.filter_by(period_id=self.period_id)

        return q

    def for_user_id(self, user_id: UUID | None) -> Self:
        return self.__class__(self.session, self.period_id, user_id,
                              self.schema_name, self.schema_config)

    def for_period_id(self, period_id: UUID | None) -> Self:
        return self.__class__(self.session, period_id, self.user_id,
                              self.schema_name, self.schema_config)

    def for_schema(
        self,
        schema: str,
        schema_config: dict[str, Any] | None = None
    ) -> Self:
        return self.__class__(self.session, self.period_id, self.user_id,
                              schema, schema_config)

    def update_attendee_name(
        self,
        attendee_id: UUID,
        attendee_name: str
    ) -> None:

        invoice_items = self.query_items()

        for item in invoice_items:
            if item.attendee_id == attendee_id:
                item.group = attendee_name

    @cached_property
    def invoice(self) -> str | None:
        # XXX used for compatibility with legacy implementation in Feriennet
        return self.period_id and self.period_id.hex or None

    @cached_property
    def username(self) -> str | None:
        # XXX used for compatibility with legacy implementation in Feriennet
        if self.user_id:
            user = self.session.query(User).with_entities(
                User.username
            ).filter_by(id=self.user_id).first()

            return user and user.username or None
        return None

    def unpaid_count(
        self,
        excluded_period_ids: Collection[UUID] | None = None
    ) -> int:

        q = self.query().with_entities(func.count(BookingPeriodInvoice.id))

        if excluded_period_ids:
            q = q.filter(
                BookingPeriodInvoice.period_id.notin_(excluded_period_ids))

        q = q.filter(BookingPeriodInvoice.paid == False)

        return q.scalar() or 0

    def add(  # type:ignore[override]
        self,
        period_id: UUID | None = None,
        user_id: UUID | None = None,
        flush: bool = True,
        optimistic: bool = False
    ) -> BookingPeriodInvoice:

        invoice = BookingPeriodInvoice(  # type: ignore[misc]
            id=uuid4(),
            period_id=period_id or self.period_id,
            user_id=user_id or self.user_id)

        self.session.add(invoice)
        self.schema.link(
            self.session, invoice, flush=flush, optimistic=optimistic)

        if flush:
            self.session.flush()

        return invoice
