from __future__ import annotations

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
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.ticket.models import Ticket
    from onegov.pay.models import InvoiceItem, PaymentProvider
    from onegov.pay.types import PaymentState
    from typing import Self


class Payment(Base, TimestampMixin, ContentMixin, Associable):
    """ Represents a payment done through various means. """

    __tablename__ = 'payments'

    #: the public id of the payment
    id: Column[uuid.UUID] = Column(
        UUID,  # type: ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the polymorphic source of the payment
    source: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    #: the amount to pay
    # FIXME: This was probably meant to be nullable=False
    amount: Column[Decimal | None] = Column(Numeric(precision=8, scale=2))

    #: the currency of the amount to pay
    currency: Column[str] = Column(Text, nullable=False, default='CHF')

    #: remote id of the payment
    remote_id: Column[str | None] = Column(Text, nullable=True)

    #: the state of the payment
    state: Column[PaymentState] = Column(
        Enum(  # type:ignore[arg-type]
            'open', 'paid', 'failed', 'cancelled', 'invoiced',
            name='payment_state'
        ),
        nullable=False,
        default='open'
    )

    #: the id of the payment provider associated with the payment
    provider_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('payment_providers.id'),
        nullable=True
    )

    #: the payment provider associated with the payment, if it is missing it
    #: means that the payment is out-of-band (say paid by cash)
    provider: relationship[PaymentProvider[Self] | None] = relationship(
        'PaymentProvider',
        back_populates='payments'
    )

    # NOTE: For now a payment is only ever associated with one ticket, but
    #       eventually we may allow merging invoices/payments for tickets
    ticket: relationship[Ticket | None] = relationship(
        'Ticket',
        back_populates='payment',
        uselist=False
    )

    __mapper_args__ = {
        'polymorphic_on': source,
        'polymorphic_identity': 'generic'
    }

    if TYPE_CHECKING:
        linked_invoice_items: relationship[list[InvoiceItem]]

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

    def _sync_state(
        self,
        remote_obj: Any | None = None,
        capture: bool = False,
    ) -> bool:
        raise NotImplementedError

    def sync_invoice_items(self) -> None:
        """ Updates the paid state of any linked invoice items. """
        for item in self.linked_invoice_items:
            item.paid = item.payments[-1].state == 'paid'

    def sync(
        self,
        remote_obj: Any | None = None,
        capture: bool = False,
        update_invoice_items: bool = True,
    ) -> None:
        """ Updates the local payment information with the information from
        the remote payment provider and optionally try to capture the payment
        if it hasn't been already.

        """
        # NOTE: Eagerly syncing the linked invoice items like this could
        #       be fairly slow, but the assumption here is, that the amount
        #       of synced payments with actual changes is fairly low, so
        #       it's not worth doing a complex batch update. Doing it
        #       eagerly avoids us having to remember where we sync
        #       payments.
        if self._sync_state(remote_obj, capture) and update_invoice_items:
            self.sync_invoice_items()


class ManualPayment(Payment):
    """ A manual payment is a payment without associated payment provider.

    For example, a payment paid in cash.

    """
    __mapper_args__ = {'polymorphic_identity': 'manual'}

    def _sync_state(
        self,
        remote_obj: None = None,
        capture: bool = False
    ) -> bool:
        return False
