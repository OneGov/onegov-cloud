from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pay.models.payment import Payment
from sqlalchemy import Column
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

    __mapper_args__ = {
        'polymorphic_on': type
    }

    payments = relationship(
        'Payment',
        order_by='Payment.created',
        backref='provider'
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
