from __future__ import annotations

from decimal import Decimal
from functools import total_ordering
from onegov.core.orm import Base


from typing import NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pay.types import PriceDict
    from sqlalchemy import Table
    from typing import Self


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
        assert self.currency is None or self.currency == other.currency
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


def payments_association_table_for(cls: type[Base]) -> Table:
    return Base.metadata.tables[f'payments_for_{cls.__tablename__}_payments']
