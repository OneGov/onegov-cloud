from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property, total_ordering
from onegov.core.orm import Base
from onegov.pay.constants import SCALE


from typing import Any, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.pay.models import Invoice, InvoiceItem
    from onegov.pay.types import PriceDict
    from sqlalchemy import Table
    from typing import Self, SupportsIndex


class _PriceBase(NamedTuple):
    amount: Decimal
    currency: str | None
    fee: Decimal
    credit_card_payment: bool


@total_ordering
class Price(_PriceBase):
    """ A single price.

    The amount includes the fee. To get the net amount use the net_amount
    property.

    """

    def __new__(
        cls,
        amount: Decimal | float,
        currency: str | None,
        fee: Decimal | float = 0,
        credit_card_payment: bool = False
    ) -> Self:
        return super().__new__(
            cls,
            Decimal(amount),
            currency,
            Decimal(fee),
            credit_card_payment
        )

    def __bool__(self) -> bool:
        return self.amount and True or False

    def __lt__(self, other: Price) -> bool:  # type:ignore[override]
        assert self.currency is None or self.currency == other.currency or (
            other.currency is None and self.currency is not None
        )
        return self.amount < other.amount

    def __add__(self, other: Price) -> Self:  # type:ignore[override]
        assert (
            (self.currency is None or other.currency is None) or
            self.currency == other.currency
        )
        cc_payment = self.credit_card_payment or other.credit_card_payment
        return self.__class__(
            self.amount + other.amount,
            self.currency or other.currency,
            credit_card_payment=cc_payment
        )

    def __sub__(self, other: Price) -> Self:
        assert self.currency == other.currency
        cc_payment = self.credit_card_payment or other.credit_card_payment
        return self.__class__(
            self.amount - other.amount,
            self.currency,
            credit_card_payment=cc_payment
        )

    def __mul__(self, other: Decimal | float | SupportsIndex) -> Self:
        assert not self.fee, 'Multipliers should be applied before fees'
        if not isinstance(other, (Decimal, float, int)):
            other = int(other)
        return self.__class__(
            self.amount * Decimal(other),
            self.currency,
            credit_card_payment=self.credit_card_payment
        )

    __rmul__ = __mul__

    def __str__(self) -> str:
        return f'{self.amount:.2f} {self.currency}'

    def __repr__(self) -> str:
        return f'Price({self.amount!r}, {self.currency!r})'

    @classmethod
    def zero(cls) -> Self:
        return cls(0, None)

    def as_dict(self) -> PriceDict:
        return {
            'amount': float(self.amount),
            'currency': self.currency,
            'fee': float(self.fee),
            'credit_card_payment': self.credit_card_payment
        }

    @property
    def net_amount(self) -> Decimal:
        return self.amount - self.fee

    def apply_discount(self, discount: Decimal) -> Self:
        assert discount <= Decimal('1')
        assert not self.fee, 'Discounts should be applied before fees'
        return self.__class__(
            self.amount - self.amount*discount,
            self.currency,
            credit_card_payment=self.credit_card_payment
        )


@dataclass(frozen=True)
class InvoiceItemMeta:
    text: str
    group: str
    unit: Decimal
    quantity: Decimal = Decimal('1')
    vat_rate: Decimal | None = None
    family: str | None = None
    cost_object: str | None = None
    extra: dict[str, Any] | None = None

    @cached_property
    def amount(self) -> Decimal:
        return round(
            round(self.unit, SCALE) * round(self.quantity, SCALE),
            SCALE
        )

    @cached_property
    def vat(self) -> Decimal:
        return self.amount - self.net_amount

    @cached_property
    def net_amount(self) -> Decimal:
        if self.vat_rate is None:
            return self.amount
        vat_factor = round(
                (self.vat_rate + Decimal('100')) / Decimal('100'),
                4
            )
        return round(self.amount / vat_factor, SCALE)

    @staticmethod
    def total(items: Iterable[InvoiceItemMeta]) -> Decimal:
        return sum((item.amount for item in items), start=Decimal('0'))

    @staticmethod
    def total_vat(items: Iterable[InvoiceItemMeta]) -> Decimal:
        return sum((item.vat for item in items), start=Decimal('0'))

    def add_to_invoice(self, invoice: Invoice) -> InvoiceItem:
        return invoice.add(
            text=self.text,
            group=self.group,
            family=self.family,
            cost_object=self.cost_object,
            unit=self.unit,
            quantity=self.quantity,
            vat_rate=self.vat_rate,
            **(self.extra or {})
        )

    def refresh_item(self, item: InvoiceItem) -> None:
        assert item.group == self.group
        assert item.family == self.family
        if item.cost_object != self.cost_object:
            item.cost_object = self.cost_object
        if item.text != self.text:
            item.text = self.text
        if item.unit != self.unit:
            item.unit = self.unit
        if item.quantity != self.quantity:
            item.quantity = self.quantity
        if item.vat_rate != self.vat_rate:
            item.vat_rate = self.vat_rate
        for attr, value in (self.extra or {}).items():
            if hasattr(item, attr) and getattr(item, attr) != value:
                setattr(item, attr, value)


class _InvoiceDiscountMetaBase(NamedTuple):
    text: str
    group: str
    discount: Decimal
    vat_rate: Decimal | None = None
    family: str | None = None
    cost_object: str | None = None
    extra: dict[str, Any] | None = None


class InvoiceDiscountMeta(_InvoiceDiscountMetaBase):

    def apply_discount(
        self,
        total: Decimal,
        remainder: Decimal
    ) -> InvoiceItemMeta:
        assert self.discount <= Decimal('1')
        # we can't discount to a negative total, so we can at most
        # discount the full remainder of the invoice
        amount = min(round(total*self.discount, SCALE), remainder)
        return InvoiceItemMeta(
            text=self.text,
            unit=-amount,
            group=self.group,
            family=self.family,
            cost_object=self.cost_object,
            vat_rate=self.vat_rate,
            extra=self.extra,
        )


def payments_association_table_for(cls: type[Base]) -> Table:
    return Base.metadata.tables[f'payments_for_{cls.__tablename__}_payments']
