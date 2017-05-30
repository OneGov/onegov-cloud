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

    @property
    def title(self):
        """ The title of the payment provider (i.e. the product name). """
        raise NotImplementedError

    @property
    def identity(self):
        """ A list of values that uniquely identify the payment provider.

        For example, a redacted list of secrets.

        """
        raise NotImplementedError
