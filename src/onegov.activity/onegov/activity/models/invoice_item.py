from onegov.activity import utils
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pay import PayableManyTimes
from onegov.user import User
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates, relationship
from sqlalchemy_utils import observes
from uuid import uuid4


class InvoiceItem(Base, TimestampMixin, PayableManyTimes):
    """ An item in an invoice. """

    __tablename__ = 'invoice_items'

    #: the public id of the invoice item
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the user who is charged
    username = Column(Text, ForeignKey('users.username'), nullable=False)
    user = relationship(User, backref="invoice_items")

    #: the invoice group (all items with the same text make one invoice)
    invoice = Column(Text, nullable=False)

    #: the code of the invoice used to identify the invoice through e-banking
    code = Column(Text, nullable=False)

    #: the item group (all items with the same text are visually grouped)
    group = Column(Text, nullable=False)

    #: a secondary group who is not necessarily grouped visually
    family = Column(Text, nullable=True)

    #: the item text
    text = Column(Text, nullable=False)

    #: true if paid
    paid = Column(Boolean, nullable=False, default=False)

    #: the transaction id if paid through a bank or online transaction
    tid = Column(Text, nullable=True)

    #: the source of the transaction id, e.g. stripe, xml
    source = Column(Text, nullable=True)

    #: the unit to pay..
    unit = Column(Numeric(precision=8, scale=2), nullable=True)

    #: ..multiplied by the quantity..
    quantity = Column(Numeric(precision=8, scale=2), nullable=True)

    #: ..together form the amount
    @hybrid_property
    def amount(self):
        return self.unit * self.quantity

    @observes('invoice', 'username')
    def invoice_username_observer(self, invoice, username):
        self.code = utils.as_invoice_code(invoice, username)

    @validates('source')
    def validate_source(self, key, value):
        assert value in (None, 'xml', 'stripe_connect')
        return value

    @property
    def display_code(self):
        """ The item's code, formatted in a human readable format. """
        return utils.format_invoice_code(self.code)

    @property
    def esr_code(self):
        """ The item's code, formatted as ESR. """
        return utils.encode_invoice_code(self.code)

    @property
    def display_esr_code(self):
        """ The item's ESR formatted in a human readable format. """
        return utils.format_esr_reference(self.esr_code)

    @property
    def discourage_changes(self):
        return self.source == 'xml'

    @property
    def disable_changes(self):
        if not self.source:
            return False

        if self.source == 'xml':
            return False

        states = {p.state for p in self.payments}
        return 'open' in states or 'paid' in states
