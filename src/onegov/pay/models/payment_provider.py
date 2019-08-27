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


class PaymentProvider(Base, TimestampMixin, ContentMixin):
    """ Represents a payment provider. """

    __tablename__ = 'payment_providers'

    #: the public id of the payment provider
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the polymorphic type of the provider
    type = Column(Text, nullable=True)

    #: true if this is the default provider (can only ever be one)
    default = Column(Boolean, nullable=False, default=False)

    __mapper_args__ = {
        'polymorphic_on': type
    }

    __table_args__ = (
        Index(
            'only_one_default_provider', 'default',
            unique=True, postgresql_where=column('default') == True
        ),
    )

    payments = relationship(
        'Payment',
        order_by='Payment.created',
        backref='provider',
        passive_deletes=True
    )

    @property
    def payment_class(self):
        assert type(self) is PaymentProvider, "Override this in subclasses"
        return Payment

    def payment(self, **kwargs):
        """ Creates a new payment using the correct model. """

        payment = self.payment_class(**kwargs)
        payment.provider = self

        return payment

    def adjust_price(self, price):
        """ Called by client implementations this method allows to adjust the
        price by adding a fee to it.

        By default no change is made.

        """

        return price

    def charge(self, amount, currency, token):
        """ Given a payment token, charges the customer and creates a payment
        which is returned.

        """
        raise NotImplementedError

    @property
    def title(self):
        """ The title of the payment provider (i.e. the product name). """
        raise NotImplementedError

    @property
    def url(self):
        """ The url to the backend of the payment provider. """
        raise NotImplementedError

    @property
    def public_identity(self):
        """ The public identifier of this payment provider. For example, the
        account name.

        """
        raise NotImplementedError

    @property
    def identity(self):
        """ Uniquely identifies this payment provider amongst other providers
        of the same type (say the private key of the api). Used to be able
        to tell if a new oauth connection is the same as an existing one.

        This identity is not meant to be displayed.

        """
        raise NotImplementedError

    @property
    def connected(self):
        """ Returns True if the provider is properly hooked up to the
        payment provider.

        """

    def checkout_button(self, label, amount, currency, action='submit',
                        **extra):
        """ Renders a checkout button which will store the token for the
        checkout as its own value if clicked.

        The action controls what happens after the token was successfully
        retrieved. The following actions are supported:

        - 'post': Submits the form surrounding the button.

        """
        raise NotImplementedError

    def prepare_oauth_request(self, redirect_url, success_url, error_url,
                              user_fields=None):
        """ Registers the oauth request with the oauth_gateway and returns
        an url that is ready to be used for the complete oauth request.

        """
        raise NotImplementedError

    def process_oauth_response(self, request_params):
        """ Processes the oauth response using the parameters passed by
        the returning oauth request via the gateway.

        """
        raise NotImplementedError
