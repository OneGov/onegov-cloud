from __future__ import annotations

import stripe


class DatatransPaymentError(Exception):
    pass


class DatatransApiError(DatatransPaymentError):

    def __init__(self, code: str, message: str, terminal: bool) -> None:
        super().__init__(f'{code}: {message}')
        self.code = code
        self.message = message
        self.terminal = terminal


class SaferpayPaymentError(Exception):
    pass


class SaferpayApiError(SaferpayPaymentError):

    def __init__(
        self,
        name: str,
        message: str,
        behavior: str,
        detail: list[str] | None = None
    ) -> None:

        details = tuple(detail) if detail else ()
        super().__init__('\n'.join((
            f'{name}: {message}',
            *details,
        )))
        self.name = name
        self.message = message
        self.behavior = behavior
        self.details = details


# the following exceptions should be caught and logged - the user should be
# informed that the payment failed, but not why
CARD_ERRORS = (
    stripe.error.CardError,
    DatatransPaymentError,
    SaferpayPaymentError,
)
