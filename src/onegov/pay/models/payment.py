from decimal import Decimal
from onegov.core.orm import Base
from onegov.core.orm.abstract.associable import Associable
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from uuid import uuid4


class Payment(Base, TimestampMixin, ContentMixin, Associable):
    """ Represents a payment done through various means. """

    __tablename__ = 'payments'

    #: the public id of the payment
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the polymorphic source of the payment
    source = Column(Text, nullable=True)

    #: the amount to pay
    amount = Column(Numeric(precision=8, scale=2))

    #: the currency of the amount to pay
    currency = Column(Text, nullable=False, default='CHF')

    #: remote id of the payment
    remote_id = Column(Text, nullable=True)

    #: the state of the payment
    state = Column(
        Enum('open', 'paid', 'failed', 'cancelled', name='payment_state'),
        nullable=False,
        default='open'
    )

    #: the payment provider associated with the payment, if it is missing it
    #: means that the payment is out-of-band (say paid by cash)
    provider_id = Column(
        UUID, ForeignKey('payment_providers.id'), nullable=True
    )

    __mapper_args__ = {
        'polymorphic_on': source
    }

    @property
    def fee(self):
        """ The fee associated with this payment. The payment amount includes
        the fee. To get the net amount use the net_amount property.

        """
        return Decimal(0)

    @property
    def net_amount(self):
        return self.amount - self.fee

    @hybrid_property
    def paid(self):
        """ Our states are essentially one paid and n unpaid states (indicating
        various ways in which the payment can end up being unpaid).

        So this boolean acts as coarse filter to divide payemnts into the
        two states that really matter.

        """
        return self.state == 'paid'

    @property
    def remote_url(self):
        """ Returns the url of this object on the payment provider. """

        raise NotImplementedError

    def sync(self, remote_obj=None):
        """ Updates the local payment information with the information from
        the remote payment provider.

        """

        raise NotImplementedError


class ManualPayment(Payment):
    """ A manual payment is a payment without associated payment provider.

    For example, a payment paid in cash.

    """
    __mapper_args__ = {'polymorphic_identity': 'manual'}

    def sync(self, remote_obj=None):
        pass
