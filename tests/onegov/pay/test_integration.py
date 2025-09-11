from __future__ import annotations

import logging

from onegov.pay import process_payment, Price
from onegov.pay import CARD_ERRORS, ManualPayment


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.capturelog import CaptureLogFixture


def test_process_manual_payment() -> None:
    payment = process_payment('manual', Price(10, 'CHF'))
    assert isinstance(payment, ManualPayment)
    assert payment.source == 'manual'
    assert payment.amount == 10
    assert payment.currency == 'CHF'

    payment = process_payment('free', Price(10, 'CHF'))
    assert isinstance(payment, ManualPayment)
    assert payment.source == 'manual'
    assert payment.amount == 10
    assert payment.currency == 'CHF'


def test_process_credit_card_payment_successfully() -> None:

    Provider: Any

    class Provider:  # type: ignore[no-redef]
        def charge(
            self,
            amount: object,
            currency: object,
            token: object
        ) -> str:
            return 'success'

    payment = process_payment('manual', Price(10, 'CHF'), Provider(), 'foobar')
    assert isinstance(payment, ManualPayment)
    assert payment.source == 'manual'

    payment = process_payment('free', Price(10, 'CHF'), Provider(), 'foobar')
    assert payment == 'success'  # type: ignore[comparison-overlap]

    payment = process_payment('cc', Price(10, 'CHF'), Provider(), 'foobar')
    assert payment == 'success'  # type: ignore[comparison-overlap]


def test_process_credit_card_payment_error(
    capturelog: CaptureLogFixture
) -> None:

    Provider: Any

    class Provider:  # type: ignore[no-redef]
        title = 'Foobar'

        def charge(
            self,
            amount: object,
            currency: object,
            token: object
        ) -> None:
            raise CARD_ERRORS[0](None, None, None)

    capturelog.setLevel(logging.ERROR, logger='onegov.pay')

    payment = process_payment('cc', Price(10, 'CHF'), Provider(), 'foobar')
    assert payment is None

    assert capturelog.records()[0].message == (
        'Processing 10.00 CHF through Foobar with token foobar failed')
