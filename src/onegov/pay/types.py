from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from decimal import Decimal
    from typing import Literal, Protocol
    from typing_extensions import TypedDict

    PaymentMethod = Literal['free', 'cc', 'manual']
    PaymentState = Literal['open', 'paid', 'failed', 'cancelled']

    class PriceDict(TypedDict):
        amount: float
        currency: str | None
        fee: float
        credit_card_payment: bool

    class FeePolicy(Protocol):
        def from_amount(self, __amount: Decimal | float) -> Decimal | float:
            ...

        def compensate(self, __amount: Decimal | float) -> Decimal | float: ...
