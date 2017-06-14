from collections import namedtuple
from decimal import Decimal
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pay.utils import QueryChain
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import Numeric
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import object_session
from uuid import uuid4


class RegisteredLink(namedtuple("RegisteredLink", ('cls', 'table', 'key'))):
    pass


class Payment(Base, TimestampMixin, ContentMixin):
    """ Represents a payment done through various means. """

    __tablename__ = 'payments'

    registered_links = {}

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

    @staticmethod
    def register_link(link_name, linked_class, association_table, table_key):
        """ The :class:`~onegov.pay.models.payable.Payable` class registers
        all back-referenes through this method. This is useful for two reasons:

        1. We gain the ability to query all the linked records in one query.
           This is hard otherwise as each ``Payable`` class leads to its own
           association table which needs to be queried separately.

        2. We are able to reset all created backreferences. This is necessary
           during tests. SQLAlchemy keeps these references around and won't
           let us re-register the same model multiple times (which outside
           of tests is completely reasonable).

        Note that this is a staticmethod instead of a classmethod because
        we want all links to be managed through the actual ``Payment`` class,
        not through any of its subclasses.

        """
        Payment.registered_links[link_name] = RegisteredLink(
            cls=linked_class,
            table=association_table,
            key=table_key
        )

    @property
    def links(self):
        session = object_session(self)

        return QueryChain(tuple(
            session.query(link.cls)
            .filter_by(payment=self)
            .options(joinedload(link.cls.payment))
            for link in self.registered_links.values()
        ))

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
