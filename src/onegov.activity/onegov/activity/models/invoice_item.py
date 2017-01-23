import hashlib

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import observes
from uuid import uuid4


class InvoiceItem(Base, TimestampMixin):
    """ An item in an invoice. """

    __tablename__ = 'invoice_items'

    #: the public id of the invoice item
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the user who is charged
    username = Column(Text, ForeignKey('users.username'), nullable=False)

    #: the invoice group (all items with the same text make one invoice)
    invoice = Column(Text, nullable=False)

    #: the code of the invoice used to identify the invoice through e-banking
    code = Column(Text, nullable=False)

    #: the item group (all items with the same text are visually grouped)
    group = Column(Text, nullable=False)

    #: the item text
    text = Column(Text, nullable=False)

    #: true if paid
    paid = Column(Boolean, nullable=False, default=False)

    #: the transaction id if paid online
    tid = Column(Text, nullable=True)

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
        # there's no guarantee that this code is unique for an invoice, though
        # the chance of it overlapping is very very small -> any algorithm
        # doing some kind of matching has to account for this fact (probably
        # by throwing an error)
        #
        # we can solve this by introducing a separate invoice record in the
        # future
        self.code = ''.join((
            hashlib.sha1((invoice + username).encode('utf-8')).hexdigest()[:5],
            hashlib.sha1(username.encode('utf-8')).hexdigest()[:5]
        ))
