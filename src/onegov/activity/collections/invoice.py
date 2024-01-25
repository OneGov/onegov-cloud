from decimal import Decimal
from functools import cached_property
from onegov.activity.models import Invoice, InvoiceItem
from onegov.activity.models.invoice import sync_invoice_items
from onegov.activity.models.invoice_reference import KNOWN_SCHEMAS, Schema
from onegov.core.collection import GenericCollection
from sqlalchemy import func, and_, not_
from sqlalchemy.orm import joinedload
from onegov.user import User
from uuid import uuid4, UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from sqlalchemy.orm import Query, Session
    from sqlalchemy.sql import ColumnElement
    from typing_extensions import Self


class InvoiceCollection(GenericCollection[Invoice]):

    def __init__(
        self,
        session: 'Session',
        period_id: UUID | None = None,
        user_id: UUID | None = None,
        schema: str = 'feriennet-v1',
        schema_config: dict[str, Any] | None = None
    ):
        super().__init__(session)
        self.user_id = user_id
        self.period_id = period_id

        if schema not in KNOWN_SCHEMAS:
            raise RuntimeError("Unknown schema: {schema}")

        self.schema_name = schema
        self.schema_config = (schema_config or {})

    @cached_property
    def schema(self) -> Schema:
        return KNOWN_SCHEMAS[self.schema_name](**self.schema_config)

    def query(self, ignore_period_id: bool = False) -> 'Query[Invoice]':
        q = super().query()

        if self.user_id:
            q = q.filter_by(user_id=self.user_id)

        if self.period_id is not None and not ignore_period_id:
            q = q.filter_by(period_id=self.period_id)

        return q

    def query_items(self) -> 'Query[InvoiceItem]':
        return self.session.query(InvoiceItem).filter(
            InvoiceItem.invoice_id.in_(
                self.query().with_entities(Invoice.id).subquery()
            )
        )

    def for_user_id(self, user_id: UUID) -> 'Self':
        return self.__class__(self.session, self.period_id, user_id,
                              self.schema_name, self.schema_config)

    def for_period_id(self, period_id: UUID) -> 'Self':
        return self.__class__(self.session, period_id, self.user_id,
                              self.schema_name, self.schema_config)

    def for_schema(
        self,
        schema: str,
        schema_config: dict[str, Any] | None = None
    ) -> 'Self':
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

    @property
    def model_class(self) -> type[Invoice]:
        return Invoice

    def _invoice_ids(self) -> 'Query[tuple[UUID]]':
        return self.query().with_entities(Invoice.id).subquery()

    def _sum(self, condition: 'ColumnElement[bool]') -> Decimal:
        q = self.session.query(func.sum(InvoiceItem.amount).label('amount'))
        q = q.filter(condition)

        return Decimal(q.scalar() or 0.0)

    @property
    def total_amount(self) -> Decimal:
        return self._sum(InvoiceItem.invoice_id.in_(self._invoice_ids()))

    @property
    def outstanding_amount(self) -> Decimal:
        return self._sum(and_(
            InvoiceItem.invoice_id.in_(self._invoice_ids()),
            InvoiceItem.paid == False
        ))

    @property
    def paid_amount(self) -> Decimal:
        return self._sum(and_(
            InvoiceItem.invoice_id.in_(self._invoice_ids()),
            InvoiceItem.paid == True
        ))

    def unpaid_count(
        self,
        excluded_period_ids: 'Collection[UUID] | None' = None
    ) -> int:

        q = self.query().with_entities(func.count(Invoice.id))

        if excluded_period_ids:
            q = q.filter(not_(Invoice.period_id.in_(excluded_period_ids)))

        q = q.filter(Invoice.paid == False)

        return q.scalar() or 0

    def sync(self) -> None:
        items = self.session.query(InvoiceItem).filter(and_(
            InvoiceItem.source != None,
            InvoiceItem.source != 'xml',
            InvoiceItem.invoice_id.in_(
                self.query().with_entities(Invoice.id).subquery()
            )
        )).options(joinedload(InvoiceItem.payments))

        sync_invoice_items(items, capture=False)

    def add(  # type:ignore[override]
        self,
        period_id: UUID | None = None,
        user_id: UUID | None = None,
        flush: bool = True,
        optimistic: bool = False
    ) -> Invoice:

        invoice = Invoice(  # type:ignore[misc]
            id=uuid4(),
            period_id=period_id or self.period_id,
            user_id=user_id or self.user_id)

        self.session.add(invoice)
        self.schema.link(
            self.session, invoice, flush=flush, optimistic=optimistic)

        if flush:
            self.session.flush()

        return invoice
