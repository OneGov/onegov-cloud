from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Literal

    PaymentMethod = Literal['free', 'cc', 'manual']
