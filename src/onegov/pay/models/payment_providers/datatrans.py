from __future__ import annotations

import requests
import transaction

from decimal import Decimal
from functools import cached_property
from markupsafe import Markup
from onegov.core.orm.mixins import dict_property, meta_property
from onegov.core.utils import append_query_param
from onegov.pay import log
from onegov.pay.errors import DatatransPaymentError, DatatransApiError
from onegov.pay.models.payment import Payment
from onegov.pay.models.payment_provider import PaymentProvider
from onegov.pay.utils import Price
from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_extra_types.currency_code import Currency  # noqa: TC002
from sqlalchemy.orm import object_session
from sqlalchemy.orm.attributes import flag_modified
from uuid import UUID, uuid4, uuid5
from wtforms.widgets import html_params


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.pay.types import FeePolicy
    from sqlalchemy.orm import relationship
    from transaction.interfaces import ITransaction


# our payment ids are generated by using the token and a UUID namespace
DATATRANS_NAMESPACE = UUID('e4d0beb6-c1e7-4a90-859f-421491470e46')


# NOTE: This is just the subset of properties we care about
class DatatransTransaction(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        alias_generator=to_camel
    )

    transaction_id: str
    merchant_id: str
    type: Literal['payment', 'credit', 'card_check']
    status: Literal[
        'initialized',
        'challenge_required',
        'challenge_ongoing',
        'authenticated',
        'authorized',
        'settled',
        'canceled',
        'transmitted',
        'failed'
    ]
    refno: str
    currency: Currency
    amount: int | None = Field(
        default=None,
        validation_alias=AliasChoices(
            AliasPath('detail', 'authorize', 'amount'),
            AliasPath('detail', 'settle', 'amount'),
        )
    )

    def raise_if_cannot_be_settled(self) -> None:
        if self.type != 'payment':
            raise DatatransPaymentError('incorrect transaction type')
        if self.status != 'authorized':
            raise DatatransPaymentError('payment was not authorized')
        if not self.amount:
            raise DatatransPaymentError('could not retrieve payment amount')


class DatatransClient:

    def __init__(
        self,
        merchant_id: str | None,
        password: str | None,
        sandbox: bool = False
    ) -> None:

        self.merchant_id = merchant_id
        self.session = requests.Session()
        if merchant_id is not None:
            self.session.auth = (merchant_id, password or '')
        self.base_url = (
            f'https://api.{"sandbox." if sandbox else ""}datatrans.com/v1'
        )

    def raise_for_status(self, res: requests.Response) -> None:
        if res.status_code == 400:
            error = res.json()['error']
            raise DatatransApiError(
                error['code'],
                error['message'],
                error.get('terminal', False)
            )
        res.raise_for_status()

    def status(self, transaction_id: str) -> DatatransTransaction:
        res = self.session.get(
            f'{self.base_url}/transactions/{transaction_id}',
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        return DatatransTransaction.model_validate_json(res.content)

    def init(
        self,
        amount: Decimal | None = None,
        currency: str = 'CHF',
        **extra: Any,
    ) -> str:
        """ Initializes a transaction and returns the transaction_id. """
        if amount is not None:
            payload = {
                'currency': currency,
                'amount': round(amount * 100),
                'refno': str(uuid4()),
                **extra
            }
        else:
            payload = {
                'currency': currency,
                'refno': str(uuid4()),
                **extra
            }

        res = self.session.post(
            f'{self.base_url}/transactions',
            json=payload,
            timeout=(5, 10)
        )
        self.raise_for_status(res)
        return res.json()['transactionId']

    def settle(self, tx: DatatransTransaction) -> None:
        tx.raise_if_cannot_be_settled()
        if tx.merchant_id != self.merchant_id:
            raise DatatransPaymentError('invalid merchant_id')

        res = self.session.post(
            f'{self.base_url}/transactions/{tx.transaction_id}/settle',
            json={
                'amount': tx.amount,
                'currency': tx.currency,
                'refno': tx.refno,
            },
            timeout=(5, 10)
        )
        self.raise_for_status(res)

    def refund(self, tx: DatatransTransaction) -> str | None:
        if tx.merchant_id != self.merchant_id:
            raise DatatransPaymentError('invalid merchant_id')
        if tx.type != 'payment':
            raise DatatransPaymentError('incorrect transaction type')

        if tx.status in ('settled', 'authorized'):
            # transaction can be cancelled
            res = self.session.post(
                f'{self.base_url}/transactions/{tx.transaction_id}/cancel',
                json={},
                timeout=(5, 10)
            )
            self.raise_for_status(res)
            return None
        elif tx.status == 'transmitted':
            # actual refund required
            res = self.session.post(
                f'{self.base_url}/transactions/{tx.transaction_id}/credit',
                json={
                    'currency': tx.currency,
                    'amount': tx.amount,
                    'refno': str(uuid4()),
                },
                timeout=(5, 10)
            )
            self.raise_for_status(res)
            return res.json()['transactionId']
        elif tx.status == 'canceled':
            # transaction is already canceled
            return None
        else:
            raise AssertionError('invalid transaction state')


class DatatransSettleManager:
    """ Settles an open datatrans charge when the transaction finishes.

    If there is an error during this step, it is logged, but the transaction
    still continues successfully.

    The user is then supposed to manually settle the charge.

    """

    transaction_manager = transaction.manager

    def __init__(
        self,
        client: DatatransClient,
        tx: DatatransTransaction,
    ) -> None:

        self.client = client
        self.tx = tx

    @classmethod
    def settle_charge(
        cls,
        client: DatatransClient,
        tx: DatatransTransaction,
    ) -> None:
        transaction.get().join(cls(client, tx))

    def sortKey(self) -> str:
        return 'datatrans_settle'

    def tpc_vote(self, transaction: ITransaction) -> None:
        # make sure the transaction is still alive
        tx = self.client.status(self.tx.transaction_id)
        # make sure nothing weird happened
        tx.raise_if_cannot_be_settled()
        assert tx.merchant_id == self.client.merchant_id
        assert tx.refno == self.tx.refno
        assert tx.currency == self.tx.currency

    def tpc_finish(self, transaction: ITransaction) -> None:
        try:
            self.client.settle(self.tx)
        except Exception:
            # we can never fail or we might end up with an inconsistent
            # database -> so must swallow any errors and report them
            log.exception(
                'Datatrans settle with transaction_id %s failed',
                self.tx.transaction_id
            )

    def commit(self, transaction: ITransaction) -> None:
        pass

    def abort(self, transaction: ITransaction) -> None:
        pass

    def tpc_begin(self, transaction: ITransaction) -> None:
        pass

    def tpc_abort(self, transaction: ITransaction) -> None:
        pass


class DatatransFeePolicy:
    """ All Datarans fee calculations in one place. """

    # TODO: There may be an additional fee based on the selected
    #       payment method based on the contract signed with the
    #       responsible financial partner, like e.g. Twint, but
    #       we can't really predict that (although maybe there is
    #       a good lower/upper bound we can use)
    # NOTE: This fixed fee currently assumes CHF
    fixed = 0.29

    @classmethod
    def from_amount(cls, amount: Decimal | float) -> float:
        return cls.fixed

    @classmethod
    def compensate(cls, amount: Decimal | float) -> float:
        return round(float(amount) + cls.fixed, 2)


class DatatransPayment(Payment):
    __mapper_args__ = {'polymorphic_identity': 'datatrans'}

    fee_policy: FeePolicy = DatatransFeePolicy

    #: the refno of the transaction
    refno: dict_property[str | None] = meta_property()

    #: the transaction ids of any refunds
    refunds: dict_property[list[str]] = meta_property(default=list)

    if TYPE_CHECKING:
        # our provider should always be DatatransProvdider, we could
        # assert if we really wanted to make sure, but it would
        # add a lot of assertions...
        provider: relationship[DatatransProvider]

    # NOTE: We don't seem to get information about fees from datatrans
    #       so the only thing we know for sure is that a customer will
    #       have to pay 0.29 CHF for every transaction to datatrans.
    @property
    def fee(self) -> Decimal:
        """ The calculated fee or the effective fee if available. """

        assert self.amount is not None
        return Decimal(self.fee_policy.from_amount(self.amount))

    @property
    def remote_url(self) -> str:
        if self.provider.livemode:
            base = 'https://admin.datatrans.com/TrDetail.jsp?tid={}'
        else:
            base = 'https://admin.sandbox.datatrans.com/TrDetail.jsp?tid={}'

        return base.format(self.remote_id)

    @property
    def transaction(self) -> DatatransTransaction:
        assert self.remote_id
        return self.provider.client.status(self.remote_id)

    def refund(self) -> str | None:
        refund = self.provider.client.refund(self.transaction)
        self.state = 'cancelled'
        if refund is not None:
            self.refunds = [*self.refunds, refund]
            flag_modified(self, 'meta')
        return refund

    def sync(self, remote_obj: DatatransTransaction | None = None) -> None:
        if self.refunds:
            refund_tx = self.provider.client.status(self.refunds[-1])
            if refund_tx.status in ('settled', 'transmitted'):
                # the refund already went through
                self.state = 'cancelled'
                return
            elif refund_tx.status not in ('failed', 'canceled'):
                # the refund is still pending, let's not update yet
                return
            # the refund failed or got canceled, so we need to use
            # the status of the original transaction

        if remote_obj is None:
            remote_obj = self.transaction

        match remote_obj.status:
            case 'transmitted':
                self.state = 'paid'

            case 'settled':
                # TODO: Do we want a separate state for this?
                pass

            case 'canceled':
                self.state = 'cancelled'

            case 'failed':
                self.state = 'failed'

            case _:
                self.state = 'open'


class DatatransProvider(PaymentProvider[DatatransPayment]):

    __mapper_args__ = {'polymorphic_identity': 'datatrans'}

    fee_policy: FeePolicy = DatatransFeePolicy

    #: Whether or not this is a Sandbox account
    sandbox: dict_property[bool] = meta_property(default=False)

    #: The public Datatrans merchant name
    merchant_name: dict_property[str | None] = meta_property()

    #: The Datatrans merchant id
    merchant_id: dict_property[str | None] = meta_property()

    #: The password used for API calls
    password: dict_property[str | None] = meta_property()

    #: The HMAC key used for signing webhook calls
    webhook_key: dict_property[str | None] = meta_property()

    #: Should the fee be charged to the customer or not?
    charge_fee_to_customer: dict_property[bool | None] = meta_property()

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
        return not self.sandbox

    @property
    def payment_class(self) -> type[DatatransPayment]:
        return DatatransPayment

    @property
    def title(self) -> str:
        return 'Datatrans'

    @property
    def url(self) -> str:
        if self.sandbox:
            return 'https://admin.sandbox.datatrans.com/'
        else:
            return 'https://admin.datatrans.com/'

    @property
    def public_identity(self) -> str:
        return self.merchant_name or ''

    @property
    def identity(self) -> str | None:
        return self.merchant_id

    @cached_property
    def client(self) -> DatatransClient:
        return DatatransClient(self.merchant_id, self.password, self.sandbox)

    @property
    def connected(self) -> bool:
        # NOTE: It seems like the only way to check this is to initialize
        #       a transaction. I'm not sure whether we can always omit the
        #       price or if it depends on which payment methods are enabled.
        #       It's not great, that we have to provide dummy urls here...
        try:
            self.client.init(
                redirect={
                    'successUrl': self.url,
                    'cancelUrl': self.url,
                    'errorUrl': self.url,
                }
            )
        except Exception:
            log.exception('Datrans connection failed')
            return False
        else:
            return True

    def charge(
        self,
        amount: Decimal,
        currency: str,
        token: str  # transaction_id
    ) -> DatatransPayment:

        # ensure the transaction can be settled
        tx = self.client.status(token)
        tx.raise_if_cannot_be_settled()
        if tx.currency != currency or tx.amount != round(amount * 100):
            raise DatatransPaymentError('Invalid payment amount')
        if not tx.refno:
            raise DatatransPaymentError('refno is missing')

        session = object_session(self)
        payment = self.payment(
            id=uuid5(DATATRANS_NAMESPACE, tx.refno),
            amount=amount,
            currency=currency,
            remote_id=token,
            refno=tx.refno,
            state='open'
        )

        assert self.merchant_id is not None
        DatatransSettleManager.settle_charge(self.client, tx)

        # we do *not* want to lose this information, so even though the
        # caller should make sure the payment is stored, we make sure
        session.add(payment)

        return payment

    def get_token(self, request: CoreRequest) -> str | None:
        """ Extracts this provider's specific token from the request. """
        token = request.params.get('datatransTrxId')
        if not isinstance(token, str):
            return None
        return token

    def checkout_button(
        self,
        label: str,
        amount: Decimal | None,
        currency: str | None,
        complete_url: str,
        request: CoreRequest,
        **extra: Any
    ) -> Markup:
        """ Generates the html for the checkout button. """

        if amount is None:
            amount = Decimal(0)
            currency = 'CHF' if currency is None else currency
        else:
            assert currency is not None

        extra_params = {}
        if locale := request.locale:
            extra_params['language'] = locale.split('_')[0]

        complete_url = append_query_param(
            complete_url,
            'session_nonce',
            request.get_session_nonce()
        )

        transaction_id = self.client.init(
            amount=amount,
            currency=currency,
            autoSettle=False,
            redirect={
                'successUrl': complete_url,
                'cancelUrl': request.url,
                'errorUrl': complete_url,
                'startTarget': '_top',
                'returnTarget': '_top',
                'method': 'POST',
            },
            webhook={
                'url': request.link(self, 'webhook'),
            },
            **extra_params
        )

        params: dict[str, Any] = {'data-transaction-id': transaction_id}
        if self.sandbox:
            params['data-sandbox'] = True

        return Markup(
            '<button class="checkout-button datatrans button"'
            '{html_params}>{label}</button>'
        ).format(
            label=label,
            html_params=Markup(html_params(**params))  # noqa: RUF035
        )

    def sync(self) -> None:
        session = object_session(self)
        query = session.query(self.payment_class)
        # TODO: We currenly only sync open payments, although it may
        #       be possible for paid payments to transition to failed
        #       or cancelled if there's a chargeback of some kind...
        #       Maybe it would be better to just sync any payment
        #       where a change occurred in the past six months.
        #       This would keep the volume of API requests bounded
        #       while yielding more accurate results, but maybe the
        #       webhook is better suited for that...
        query = query.filter(self.payment_class.state == 'open')
        for payment in query:
            payment.sync()
