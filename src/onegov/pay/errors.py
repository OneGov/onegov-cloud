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

    # the following errors should be fine to ignore on our end
    # full list of names: https://saferpay.github.io/jsonapi/#errorhandling
    EXPECTED_ERROR_NAMES = frozenset((
        'BLOCKED_BY_RISK_MANAGEMENT',
        'CARD_CHECK_FAILED',
        'CARD_CVC_INVALID',
        'CARD_CVC_REQUIRED',
        'COMMUNICATION_FAILED',
        'COMMUNICATION_TIMEOUT',
        'GENERAL_DECLINED',
        'PAYER_AUTHENTICATION_REQUIRED',
        'PAYMENTMEANS_INVALID',
        'PAYMENTMEANS_NOT_SUPPORTED',
        '3DS_AUTHENTICATION_FAILED',
        'TRANSACTION_ABORTED',
        'TRANSACTION_DECLINED',
        'UNEXPECTED_ERROR_BY_ACQUIRER',
        'UPDATE_CARD_INFORMATION',
    ))

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

    @property
    def is_expected_failure(self) -> bool:
        return self.name in self.EXPECTED_ERROR_NAMES


# the following exceptions should be caught and logged - the user should be
# informed that the payment failed, but not why
CARD_ERRORS = (
    stripe.error.CardError,
    DatatransPaymentError,
    SaferpayPaymentError,
)
