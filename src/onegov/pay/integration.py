from __future__ import annotations

from enum import IntEnum
from more.webassets import WebassetsApp
from onegov.core.orm.cache import request_cached
from onegov.pay import log
from onegov.pay import PaymentProvider
from onegov.pay.errors import CARD_ERRORS
from onegov.pay.models.payment import ManualPayment
from onegov.pay.utils import Price


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from functools import cached_property
    from onegov.pay.models.payment import Payment
    from onegov.pay.types import PaymentMethod
    from sqlalchemy.orm import Session


class PayApp(WebassetsApp):
    """ Provides payment integration for
    :class:`onegov.core.framework.Framework` based applications.

    """

    if TYPE_CHECKING:
        # forward declare the attributes from Framework we depend on
        @cached_property
        def session(self) -> Callable[[], Session]: ...

    def configure_payment_providers(
        self,
        *,
        payment_providers_enabled: bool = False,
        payment_provider_defaults: dict[str, Any] | None = None,
        **cfg: Any
    ) -> None:
        """ Configures the preconfigured parameters for payment providers.

        Takes one dictionary for each availble provider. Available providers
        can be found in the models/payment_providers folder. Additionally,
        it is possible to enable/disable custom payment providers for the
        whole site.

        For example::

            payment_providers_enabled: true
            payment_provider_defaults:
                stripe_connect:
                    client_id: foo
                    client_secret: bar

        Since multiple payment providers (even of the same type) may exist,
        and because some information stored on the payment providers need
        to be configured differently for each application_id (and possibly
        set up through OAuth) we only provide default parameters.

        When we create a new payment provider, these default values may be
        read by the payment provider.

        """

        self.payment_providers_enabled = payment_providers_enabled

        self.payment_provider_defaults = payment_provider_defaults or {}

    # NOTE: This is another model where we could probably get away with a
    #       more long-term cache, but again, we have to prove it's worth it
    @request_cached  # type:ignore[type-var]
    def default_payment_provider(self) -> PaymentProvider[Any] | None:
        return self.session().query(PaymentProvider).filter(
            PaymentProvider.default.is_(True),
            PaymentProvider.enabled.is_(True),
        ).first()

    def adjust_price(self, price: Price | None) -> Price | None:
        """ Takes the given price object and adjusts it depending on the
        settings of the payment provider (for example, the fee might be
        charged to the user).

        """

        if price and price.amount < 0:
            # if we somehow got a negative price, treat it the same as no price
            return Price(0, price.currency)

        if self.default_payment_provider:
            return self.default_payment_provider.adjust_price(price)

        return price


@PayApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@PayApp.webasset('pay')
def get_pay_assets() -> Iterator[str]:
    yield 'datatrans.js'
    yield 'stripe.js'
    yield 'worldline_saferpay.js'


class PaymentError(IntEnum):
    INSUFFICIENT_FUNDS = 1
    TRANSACTION_ABORTED = 2


INSUFFICIENT_FUNDS = PaymentError.INSUFFICIENT_FUNDS
TRANSACTION_ABORTED = PaymentError.TRANSACTION_ABORTED


def process_payment(
    method: PaymentMethod,
    price: Price,
    provider: PaymentProvider[Any] | None = None,
    token: str | None = None
) -> Payment | PaymentError | None:
    """ Processes a payment using various methods.

    This method returns one of the following:

        * The processed payment if successful.
        * None if an unknown error occurred.
        * An error code (see below).

    Possible error codes:

        * INSUFFICIENT_FUNDS - the card has insufficient funds.

    Available methods:

        'free': Payment may be done manually or by credit card
        'cc': Payment must be done by credit card
        'manual': Payment must be done manually

    """

    assert method in ('free', 'cc', 'manual') and price.amount > 0

    if method == 'free':
        method = 'cc' if token else 'manual'

    # FIXME: This is kind of bad, we have a default currency of CHF
    #        for None which either results in an Exception or just
    #        gets quietly applied depending on whether or not we
    #        create a ManualPayment or charge through a PaymentProvider
    #        for now let's always default to CHF, but we should be
    #        more careful about distinguishing between a Price with
    #        and without currency and force people to pass a price
    #        with a currency into this function
    currency = price.currency or 'CHF'

    if method == 'manual':
        return ManualPayment(
            amount=price.net_amount,
            currency=currency
        )

    if method == 'cc' and token:
        assert provider is not None
        try:
            return provider.charge(
                amount=price.amount,
                currency=currency,
                token=token
            )
        except CARD_ERRORS as e:

            err = str(e).lower()

            if 'insufficient funds' in err:
                return INSUFFICIENT_FUNDS

            if (
                getattr(e, 'is_expected_failure', False)
                or 'transaction aborted' in err
            ):
                return TRANSACTION_ABORTED

            log.exception(
                f'Processing {price} through {provider.title} '
                f'with token {token} failed'
            )

    return None
