from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from decimal import Decimal
    from onegov.core.orm import Base
    from onegov.pay.models import Payable, PayableManyTimes
    from typing import type_check_only, Literal, Protocol, TypeAlias, TypedDict

    PaymentMethod: TypeAlias = Literal['free', 'cc', 'manual']
    PaymentState: TypeAlias = Literal[
    'open', 'paid', 'failed', 'cancelled', 'invoiced']

    class PriceDict(TypedDict):
        amount: float
        currency: str | None
        fee: float
        credit_card_payment: bool

    class FeePolicy(Protocol):
        def from_amount(self, amount: Decimal | float, /) -> Decimal | float:
            ...

        def compensate(self, amount: Decimal | float, /) -> Decimal | float:
            ...

    # NOTE: We would like to use intersections here than pseudo classes
    @type_check_only
    class PayableBase(Base, Payable):
        pass

    @type_check_only
    class PayableManyTimesBase(Base, PayableManyTimes):
        pass

    AnyPayableBase: TypeAlias = PayableBase | PayableManyTimesBase
