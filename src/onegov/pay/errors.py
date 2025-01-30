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


# the following exceptions should be caught and logged - the user should be
# informed that the payment failed, but not why
CARD_ERRORS = (
    stripe.error.CardError,
    DatatransPaymentError,
)
