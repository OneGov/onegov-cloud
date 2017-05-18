from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy import Unicode
from sqlalchemy_utils import generic_relationship
from uuid import uuid4


class Payment(Base, TimestampMixin):
    """ A generic payment which may be attached to any other model that
    uses a UUID as a primary key.

    """

    __tablename__ = 'payments'

    #: the public id of the payment
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the polymorphic source of the payment
    source = Column(Text, nullable=False)

    #: the amount to pay
    amount = Column(Numeric(precision=8, scale=2))

    #: the currency of the amount to pay
    currency = Column(Text, nullable=False, default='CHF')

    #: the state of the payment
    state = Column(
        Enum(('open', 'paid', 'failed', 'cancelled'), name='payment_state'),
        nullable=False,
        default='open'
    )

    #: the type(s) of the link(s) to this payment
    link_type = Column(Unicode(255))

    #: the id(s) of the link(s) to this payment
    link_id = Column(Integer)

    #: each payment may link to 0-n other records (not enforced by database)
    link = generic_relationship(link_type, link_id)

    __mapper_args__ = {
        'polymorphic_on': source
    }
