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


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.pay.models import PaymentProvider
    from onegov.pay.types import PaymentState
    from sqlalchemy.orm import relationship
    from typing_extensions import Self


class Payment(Base, TimestampMixin, ContentMixin, Associable):
    """ Represents a payment done through various means. """

    __tablename__ = 'payments'

    #: the public id of the payment
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type: ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the polymorphic source of the payment
    source: 'Column[str]' = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    #: the amount to pay
    # FIXME: This was probably meant to be nullable=False
    amount: 'Column[Decimal | None]' = Column(Numeric(precision=8, scale=2))

    #: the currency of the amount to pay
    currency: 'Column[str]' = Column(Text, nullable=False, default='CHF')

    #: remote id of the payment
    remote_id: 'Column[str | None]' = Column(Text, nullable=True)

    #: the state of the payment
    state: 'Column[PaymentState]' = Column(
        Enum(  # type:ignore[arg-type]
            'open', 'paid', 'failed', 'cancelled',
            name='payment_state'
        ),
        nullable=False,
        default='open'
    )

    #: the payment provider associated with the payment, if it is missing it
    #: means that the payment is out-of-band (say paid by cash)
    provider_id: 'Column[uuid.UUID | None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('payment_providers.id'),
        nullable=True
    )

    if TYPE_CHECKING:
        # inserted via backref
        provider: relationship[PaymentProvider['Self'] | None]

    __mapper_args__ = {
        'polymorphic_on': source,
        'polymorphic_identity': 'generic'
    }

    @property
    def fee(self) -> Decimal:
        """ The fee associated with this payment. The payment amount includes
        the fee. To get the net amount use the net_amount property.

        """
        return Decimal(0)

    @property
    def net_amount(self) -> Decimal:
        assert self.amount is not None
        return Decimal(self.amount) - self.fee

    @hybrid_property
    def paid(self) -> bool:
        """ Our states are essentially one paid and n unpaid states (indicating
        various ways in which the payment can end up being unpaid).

        So this boolean acts as coarse filter to divide payemnts into the
        two states that really matter.

        """
        return self.state == 'paid'

    @property
    def remote_url(self) -> str:
        """ Returns the url of this object on the payment provider. """

        raise NotImplementedError

    def sync(self, remote_obj: Any | None = None) -> None:
        """ Updates the local payment information with the information from
        the remote payment provider.

        """

        raise NotImplementedError


class ManualPayment(Payment):
    """ A manual payment is a payment without associated payment provider.

    For example, a payment paid in cash.

    """
    __mapper_args__ = {'polymorphic_identity': 'manual'}

    def sync(self, remote_obj: None = None) -> None:
        pass
