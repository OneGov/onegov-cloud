from __future__ import annotations

from decimal import Decimal
from onegov.core.collection import GenericCollection
from onegov.pay.models.invoice import Invoice
from onegov.pay.models.invoice_item import InvoiceItem
from sqlalchemy import func, and_
from uuid import uuid4, UUID


from typing import overload, Any, Literal, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from sqlalchemy.sql import ColumnElement


InvoiceT = TypeVar('InvoiceT', bound=Invoice)
ItemT = TypeVar('ItemT', bound=InvoiceItem)


class InvoiceCollection(GenericCollection[InvoiceT], Generic[InvoiceT, ItemT]):

    @overload
    def __init__(
        self: InvoiceCollection[Invoice, InvoiceItem],
        session: Session,
        type: Literal['*', 'generic'] = '*',
        item_type: Literal['*', 'generic'] = '*'
    ) -> None: ...

    @overload
    def __init__(
        self,
        session: Session,
        type: str,
        item_type: str
    ) -> None: ...

    def __init__(
        self,
        session: Session,
        type: str = '*',
        item_type: str = '*'
    ) -> None:
        super().__init__(session)
        self.type = type
        self.item_type = item_type

    @property
    def model_class(self) -> type[InvoiceT]:
        if self.type == '*':
            return Invoice  # type: ignore[return-value]
        return Invoice.get_polymorphic_class(self.type, Invoice)  # type: ignore[arg-type, return-value]

    @property
    def item_model_class(self) -> type[ItemT]:
        if self.item_type == '*':
            return InvoiceItem  # type: ignore[return-value]
        return InvoiceItem.get_polymorphic_class(self.item_type, InvoiceItem)  # type: ignore[arg-type, return-value]

    def query(self) -> Query[InvoiceT]:
        Invoice = self.model_class  # noqa: N806

        query = super().query()

        if self.type != '*':
            query = query.filter(Invoice.type == self.type)

        return query

    def query_items(self) -> Query[ItemT]:
        Invoice = self.model_class  # noqa: N806
        InvoiceItem = self.item_model_class  # noqa: N806

        query = self.session.query(self.item_model_class).filter(
            InvoiceItem.invoice_id.in_(
                self.query().with_entities(Invoice.id).scalar_subquery()
            )
        )

        if self.item_type != '*':
            query = query.filter(InvoiceItem.type == self.item_type)

        return query

    def _invoice_ids(self) -> Query[tuple[UUID]]:
        Invoice = self.model_class  # noqa: N806
        return self.query().with_entities(Invoice.id).scalar_subquery()

    def _sum(self, condition: ColumnElement[bool]) -> Decimal:
        InvoiceItem = self.item_model_class  # noqa: N806
        q = self.session.query(func.sum(InvoiceItem.amount))
        q = q.filter(condition)

        return Decimal(q.scalar() or 0.0)

    @property
    def total_amount(self) -> Decimal:
        InvoiceItem = self.item_model_class  # noqa: N806
        return self._sum(InvoiceItem.invoice_id.in_(self._invoice_ids())
        )

    @property
    def outstanding_amount(self) -> Decimal:
        InvoiceItem = self.item_model_class  # noqa: N806
        return self._sum(and_(
            InvoiceItem.invoice_id.in_(self._invoice_ids()),
            InvoiceItem.paid == False
        ))

    @property
    def paid_amount(self) -> Decimal:
        InvoiceItem = self.item_model_class  # noqa: N806
        return self._sum(and_(
            InvoiceItem.invoice_id.in_(self._invoice_ids()),
            InvoiceItem.paid == True
        ))

    def unpaid_count(self) -> int:
        Invoice = self.model_class  # noqa: N806
        query = self.query().with_entities(func.count(Invoice.id))
        query = query.filter(Invoice.paid == False)
        return query.scalar() or 0

    def add(
        self,
        flush: bool = True,
        **kwargs: Any
    ) -> InvoiceT:

        invoice = self.model_class(id=uuid4(), **kwargs)

        self.session.add(invoice)

        if flush:
            self.session.flush()

        return invoice
