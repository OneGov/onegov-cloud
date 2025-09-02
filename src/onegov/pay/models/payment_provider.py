from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pay.models.payment import Payment
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import column
from sqlalchemy import Index
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Any, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    # we are shadowing type below
    from builtins import type as _type
    from collections.abc import Mapping
    from decimal import Decimal
    from markupsafe import Markup
    from onegov.core.request import CoreRequest
    from onegov.pay import Price
    from onegov.pay.types import PaymentState

    _P = TypeVar('_P', bound=Payment, default=Payment)
else:
    _P = TypeVar('_P', bound=Payment)


class PaymentProvider(Base, TimestampMixin, ContentMixin, Generic[_P]):
    """ Represents a payment provider. """

    __tablename__ = 'payment_providers'

    #: the public id of the payment provider
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the polymorphic type of the provider
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    #: true if this is the default provider (can only ever be one)
    default: Column[bool] = Column(Boolean, nullable=False, default=False)

    #: true if this provider is enabled
    enabled: Column[bool] = Column(Boolean, nullable=False, default=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic'
    }

    __table_args__ = (
        Index(
            'only_one_default_provider', 'default',
            unique=True, postgresql_where=column('default') == True
        ),
    )

    payments: relationship[list[Payment]] = relationship(
        'Payment',
        order_by='Payment.created',
        back_populates='provider',
        passive_deletes=True
    )

    if TYPE_CHECKING:
        @property
        def payment_class(self) -> _type[_P]: ...
    else:
        @property
        def payment_class(self) -> _type[Payment]:
            assert type(self) is PaymentProvider, 'Override this in subclasses'
            return Payment

    def payment(
        self,
        *,
        amount: Decimal | None = None,
        currency: str = 'CHF',
        remote_id: str | None = None,
        state: PaymentState = 'open',
        # FIXME: We probably don't want to allow arbitrary kwargs
        #        but we need to make sure, we don't use any other
        #        one somewhere first
        **kwargs: Any
    ) -> _P:
        """ Creates a new payment using the correct model. """

        payment = self.payment_class(
            amount=amount,
            currency=currency,
            remote_id=remote_id,
            state=state,
            **kwargs
        )
        payment.provider = self

        return payment

    def adjust_price(self, price: Price | None) -> Price | None:
        """ Called by client implementations this method allows to adjust the
        price by adding a fee to it.

        By default no change is made.

        """

        return price

    def charge(self, amount: Decimal, currency: str, token: str) -> Payment:
        """ Given a payment token, charges the customer and creates a payment
        which is returned.

        """
        raise NotImplementedError

    @property
    def title(self) -> str:
        """ The title of the payment provider (i.e. the product name). """
        raise NotImplementedError

    @property
    def url(self) -> str:
        """ The url to the backend of the payment provider. """
        raise NotImplementedError

    @property
    def public_identity(self) -> str:
        """ The public identifier of this payment provider. For example, the
        account name.

        """
        raise NotImplementedError

    @property
    def identity(self) -> str | None:
        """ Uniquely identifies this payment provider amongst other providers
        of the same type (say the private key of the api). Used to be able
        to tell if a new oauth connection is the same as an existing one.

        This identity is not meant to be displayed.

        """
        raise NotImplementedError

    @property
    def connected(self) -> bool:
        """ Returns True if the provider is properly hooked up to the
        payment provider.

        """
        return False

    def get_token(self, request: CoreRequest) -> str | None:
        """ Extracts this provider's specific token from the request. """
        raise NotImplementedError

    def checkout_button(
        self,
        label: str,
        amount: Decimal | None,
        currency: str | None,
        complete_url: str,
        request: CoreRequest,
        **extra: Any
    ) -> Markup:
        """ Renders a checkout button. """
        raise NotImplementedError

    def prepare_oauth_request(
        self,
        redirect_url: str,
        success_url: str,
        error_url: str,
        user_fields: dict[str, Any] | None = None
    ) -> str:
        """ Registers the oauth request with the oauth_gateway and returns
        an url that is ready to be used for the complete oauth request.

        """
        raise NotImplementedError

    def process_oauth_response(
        self,
        request_params: Mapping[str, Any]
    ) -> None:
        """ Processes the oauth response using the parameters passed by
        the returning oauth request via the gateway.

        """
        raise NotImplementedError

    def sync(self) -> None:
        """ Updates the local payment information with the information from
        the remote payment provider.

        """

    @property
    def payment_via_get(self) -> bool:
        """
        Whether or not we're allowed to submit a payment via `GET` request.

        Ideally this is always `False`, but some payment providers only
        support a redirect via `GET`. Make sure the token retrieval is
        sufficiently secure to make up for this shortcoming.
        """
        return False
