import requests
import stripe
import transaction

from cached_property import cached_property
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from html import escape
from onegov.core.orm.mixins import meta_property
from onegov.pay import log
from onegov.pay.models.payment import Payment
from onegov.pay.models.payment_provider import PaymentProvider
from onegov.pay.utils import Price
from sqlalchemy.orm import object_session
from uuid import UUID, uuid4, uuid5


from typing import Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Callable, Iterator, Mapping
    from onegov.core.orm.mixins import dict_property
    from onegov.pay.types import FeePolicy
    from sqlalchemy.orm import relationship, Query, Session
    # NOTE: Technically this could be overwritten by anything that
    #       satisfies the ITransaction interface, but we are happier
    #       not having to deal with the zope.interface mypy plugin
    from transaction import Transaction
    from typing_extensions import ParamSpec

    _R = TypeVar('_R', bound=stripe.api_resources.abstract.ListableAPIResource)
    _P = ParamSpec('_P')


@contextmanager
def stripe_api_key(key: str | None) -> 'Iterator[None]':
    old_key = stripe.api_key
    stripe.api_key = key
    yield
    stripe.api_key = old_key


# instantiate once to get keep-alive support
stripe.default_http_client = stripe.http_client.RequestsClient()


# our stripe payment ids are generated by using the token and a UUID namespace
STRIPE_NAMESPACE = UUID('aebb1a32-282b-4521-838d-92a1136624d1')


class StripeCaptureManager:
    """ Captures an open stripe charge when the transaction finishes.

    If there is an error during this step, it is logged, but the transaction
    still continues successfully.

    The user is then supposed to manually capture the charge.

    """

    transaction_manager = transaction.manager

    def __init__(self, api_key: str, charge_id: str):
        self.api_key = api_key
        self.charge_id = charge_id

    @classmethod
    def capture_charge(cls, api_key: str, charge_id: str) -> None:
        transaction.get().join(cls(api_key, charge_id))

    def sortKey(self) -> str:
        return 'charge'

    def tpc_vote(self, transaction: 'Transaction') -> None:
        with stripe_api_key(self.api_key):
            self.charge = stripe.Charge.retrieve(self.charge_id)

    def tpc_finish(self, transaction: 'Transaction') -> None:
        try:
            with stripe_api_key(self.api_key):
                self.charge.capture()
        except Exception:
            # we can never fail or we might end up with an incosistent
            # database -> so must swallow any errors and report them
            log.exception("Stripe charge with capture id {} failed".format(
                self.charge_id
            ))

    def commit(self, transaction: 'Transaction') -> None:
        pass

    def abort(self, transaction: 'Transaction') -> None:
        pass

    def tpc_begin(self, transaction: 'Transaction') -> None:
        pass

    def tpc_abort(self, transaction: 'Transaction') -> None:
        pass


class StripeFeePolicy:
    """ All stripe fee calculations in one place (should they ever change). """

    percentage = 0.029
    fixed = 0.3

    @classmethod
    def from_amount(cls, amount: Decimal | float) -> float:
        """ Gets the fee for the given amount. """

        return round(float(amount) * cls.percentage + cls.fixed, 2)

    @classmethod
    def compensate(cls, amount: Decimal | float) -> float:
        """ Increases the amount in such a way that the stripe fee is included
        in the effective charge (that is, the user paying the charge is paying
        the fee as well).

        """

        return round((float(amount) + cls.fixed) / (1 - cls.percentage), 2)


class StripePayment(Payment):
    __mapper_args__ = {'polymorphic_identity': 'stripe_connect'}

    fee_policy: 'FeePolicy' = StripeFeePolicy

    #: the date of the payout
    payout_date: 'dict_property[datetime]' = meta_property()

    #: the id of the payout
    payout_id: 'dict_property[str]' = meta_property()

    #: the fee deducted by stripe
    effective_fee: 'dict_property[float]' = meta_property()

    if TYPE_CHECKING:
        # our provider should always be StripeConnect, we could
        # assert if we really wanted to make sure, but it would
        # add a lot of assertions...
        provider: relationship['StripeConnect']

    @property
    def fee(self) -> Decimal:
        """ The calculated fee or the effective fee if available.

        The effective fee is taken from the payout records. In practice
        these values should always be the same.

        """

        if self.effective_fee:
            return Decimal(self.effective_fee)

        assert self.amount is not None
        return Decimal(self.fee_policy.from_amount(self.amount))

    @property
    def remote_url(self) -> str:
        if self.provider.livemode:
            base = 'https://dashboard.stripe.com/payments/{}'
        else:
            base = 'https://dashboard.stripe.com/test/payments/{}'

        return base.format(self.remote_id)

    @property
    def charge(self) -> stripe.Charge:
        with stripe_api_key(self.provider.access_token):
            return stripe.Charge.retrieve(self.remote_id)

    def refund(self) -> stripe.Refund:
        with stripe_api_key(self.provider.access_token):
            refund = stripe.Refund.create(charge=self.remote_id)
            self.state = 'cancelled'
            return refund

    def sync(self, remote_obj: stripe.Charge | None = None) -> None:
        charge = remote_obj or self.charge

        if not charge.captured:
            self.state = 'open'

        elif charge.refunded:
            self.state = 'cancelled'

        elif charge.status == 'failed':
            self.state = 'failed'

        elif charge.captured and charge.paid:
            self.state = 'paid'


class StripeConnect(PaymentProvider[StripePayment]):

    __mapper_args__ = {'polymorphic_identity': 'stripe_connect'}

    fee_policy: 'FeePolicy' = StripeFeePolicy

    #: The Stripe Connect client id
    client_id: 'dict_property[str]' = meta_property()

    #: The API key of the connect user
    client_secret: 'dict_property[str]' = meta_property()

    #: The oauth_redirect gateway in use (see seantis/oauth_redirect on github)
    oauth_gateway: 'dict_property[str]' = meta_property()

    #: The auth code required by oauth_redirect
    oauth_gateway_auth: 'dict_property[str]' = meta_property()

    #: The oauth_redirect secret that should be used
    oauth_gateway_secret: 'dict_property[str]' = meta_property()

    #: The authorization code provided by OAuth
    authorization_code: 'dict_property[str]' = meta_property()

    #: The public stripe key
    publishable_key: 'dict_property[str]' = meta_property()

    #: The stripe user id as confirmed by OAuth
    user_id: 'dict_property[str]' = meta_property()

    #: The refresh token provided by OAuth
    refresh_token: 'dict_property[str]' = meta_property()

    #: The access token provieded by OAuth
    access_token: 'dict_property[str]' = meta_property()

    #: The id of the latest processed balance transaction
    latest_payout: 'dict_property[stripe.Payout]' = meta_property()

    #: Should the fee be charged to the customer or not?
    charge_fee_to_customer: 'dict_property[bool]' = meta_property()

    def adjust_price(self, price: Price | None) -> Price | None:
        if price and self.charge_fee_to_customer:
            new_price = self.fee_policy.compensate(price.amount)
            new_fee = self.fee_policy.from_amount(new_price)

            return Price(
                new_price,
                price.currency,
                new_fee,
                price.credit_card_payment
            )

        return price

    @property
    def livemode(self) -> bool:
        assert self.access_token is not None
        return not self.access_token.startswith('sk_test')

    @property
    def payment_class(self) -> type[StripePayment]:
        return StripePayment

    @property
    def title(self) -> str:
        return 'Stripe Connect'

    @property
    def url(self) -> str:
        return 'https://dashboard.stripe.com/'

    @property
    def public_identity(self) -> str:
        account = self.account
        assert account is not None
        if account.business_name:
            return f'{account.business_name} / {account.email}'
        return account.email

    @property
    def identity(self) -> str | None:
        return self.user_id

    @cached_property
    def account(self) -> stripe.Account | None:
        with stripe_api_key(self.access_token):
            return stripe.Account.retrieve(id=self.user_id)

    @property
    def connected(self) -> bool:
        return self.account and True or False

    def charge(
        self,
        amount: Decimal,
        currency: str,
        token: str
    ) -> StripePayment:

        session = object_session(self)
        payment = self.payment(
            id=uuid5(STRIPE_NAMESPACE, token),
            amount=amount,
            currency=currency,
            state='open'
        )

        with stripe_api_key(self.access_token):
            charge = stripe.Charge.create(
                amount=round(amount * 100, 0),
                currency=currency,
                source=token,
                capture=False,
                idempotency_key=token,
                metadata={
                    'payment_id': payment.id.hex
                }
            )

        assert self.access_token is not None
        StripeCaptureManager.capture_charge(self.access_token, charge.id)
        payment.remote_id = charge.id

        # we do *not* want to lose this information, so even though the
        # caller should make sure the payment is stored, we make sure
        session.add(payment)

        return payment

    def checkout_button(
        self,
        label: str,
        amount: Decimal,
        currency: str,
        action: str = 'submit',
        **extra: Any
    ) -> str:
        """ Generates the html for the checkout button. """

        extra['amount'] = round(amount * 100, 0)
        extra['currency'] = currency
        extra['key'] = self.publishable_key

        attrs = {
            'data-stripe-{}'.format(key): str(value)
            for key, value in extra.items()
        }
        attrs['data-action'] = action

        return """
            <input type="hidden" name="payment_token" id="{target}">
            <button class="checkout-button stripe-connect button"
                    data-target-id="{target}"
                    {attrs}>{label}</button>
        """.format(
            label=escape(label),
            attrs=' '.join(
                '{}="{}"'.format(escape(k), escape(v))
                for k, v in attrs.items()
            ),
            target=uuid4().hex
        )

    def oauth_url(
        self,
        redirect_uri: str,
        state: str | None = None,
        user_fields: dict[str, Any] | None = None
    ) -> str:
        """ Generates an oauth url to be shown in the browser. """

        return stripe.OAuth.authorize_url(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope='read_write',
            redirect_uri=redirect_uri,
            stripe_user=user_fields,
            state=state
        )

    def prepare_oauth_request(
        self,
        redirect_uri: str,
        success_url: str,
        error_url: str,
        user_fields: dict[str, Any] | None = None
    ) -> str:
        """ Registers the oauth request with the oauth_gateway and returns
        an url that is ready to be used for the complete oauth request.

        """
        assert (self.oauth_gateway
                and self.oauth_gateway_auth
                and self.oauth_gateway_secret)

        register = f'{self.oauth_gateway}/register/{self.oauth_gateway_auth}'
        payload = {
            'url': redirect_uri,
            'secret': self.oauth_gateway_secret,
            'method': 'GET',
            'success_url': success_url,
            'error_url': error_url
        }

        response = requests.post(register, json=payload, timeout=60)
        assert response.status_code == 200

        return self.oauth_url(
            redirect_uri='{}/redirect'.format(self.oauth_gateway),
            state=response.json()['token'],
            user_fields=user_fields
        )

    def process_oauth_response(
        self,
        request_params: 'Mapping[str, Any]'
    ) -> None:
        """ Takes the parameters of an incoming oauth request and stores
        them on the payment provider if successful.

        """

        if 'error' in request_params:
            raise RuntimeError("Stripe OAuth request failed ({}: {})".format(
                request_params['error'], request_params['error_description']
            ))

        assert request_params['oauth_redirect_secret'] \
            == self.oauth_gateway_secret

        self.authorization_code = request_params['code']

        with stripe_api_key(self.client_secret):
            data = stripe.OAuth.token(
                grant_type='authorization_code',
                code=self.authorization_code,
            )

        assert data['scope'] == 'read_write'

        self.publishable_key = data['stripe_publishable_key']
        self.user_id = data['stripe_user_id']
        self.refresh_token = data['refresh_token']
        self.access_token = data['access_token']

    def sync(self) -> None:
        session = object_session(self)
        self.sync_payment_states(session)
        self.sync_payouts(session)

    def sync_payment_states(self, session: 'Session') -> None:

        def payments(ids: 'Collection[UUID]') -> 'Query[StripePayment]':
            q = session.query(self.payment_class)
            q = q.filter(self.payment_class.id.in_(ids))

            return q

        def include_charge(charge: stripe.Charge) -> bool:
            return 'payment' in charge.metadata

        charges = self.paged(
            stripe.Charge.list,
            limit=100,
            include=include_charge
        )

        by_payment = {
            charge.metadata['payment_id']: charge
            for charge in charges
        }

        for payment in payments(by_payment.keys()):
            payment.sync(remote_obj=by_payment[payment.id.hex])

    def sync_payouts(self, session: 'Session') -> None:
        """
        see https://stripe.com/docs/api/balance_transactions/list
        and https://stripe.com/docs/api/payouts
        """

        payouts: 'Iterator[stripe.Payout]' = self.paged(
            stripe.Payout.list, limit=100, status='paid'
        )
        latest_payout = None

        paid_charges = {}

        for payout in payouts:
            if latest_payout is None:
                latest_payout = payout

            if payout.id == self.latest_payout:
                break

            # We have to skip payouts that were manually triggered
            # otherwise resulting in error with http_status of 400
            if not payout.automatic:
                continue

            transactions: 'Iterator[stripe.BalanceTransaction]' = self.paged(
                stripe.BalanceTransaction.list,
                limit=100,
                payout=payout.id,
                type='charge'
            )
            for charge in transactions:
                paid_charges[charge.source] = (
                    datetime.fromtimestamp(payout.arrival_date),
                    payout.id,
                    charge.fee / 100
                )

        if paid_charges:
            q = session.query(self.payment_class)
            q = q.filter(self.payment_class.remote_id.in_(paid_charges.keys()))

            for p in q:
                p.payout_date, p.payout_id, p.effective_fee\
                    = paid_charges[p.remote_id]

        self.latest_payout = latest_payout and latest_payout.id

    def paged(
        self,
        method: 'Callable[_P, stripe.ListObject]',
        include: 'Callable[[_R], bool]' = lambda record: True,
        *args: '_P.args',
        **kwargs: '_P.kwargs'
    ) -> 'Iterator[_R]':
        with stripe_api_key(self.access_token):
            list_obj = method(*args, **kwargs)
            records = (r for r in list_obj.auto_paging_iter())
            records = (r for r in records if include(r))

            yield from records
