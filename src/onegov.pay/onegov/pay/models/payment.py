from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import event
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapper
from sqlalchemy.orm.attributes import InstrumentedAttribute
from uuid import uuid4


class Payment(Base, TimestampMixin, ContentMixin):
    """ Represents a payment done through various means. """

    __tablename__ = 'payments'

    linked_classes = []

    #: the public id of the payment
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the polymorphic source of the payment
    source = Column(Text, nullable=True)

    #: the amount to pay
    amount = Column(Numeric(precision=8, scale=2))

    #: the currency of the amount to pay
    currency = Column(Text, nullable=False, default='CHF')

    #: the state of the payment
    state = Column(
        Enum('open', 'paid', 'failed', 'cancelled', name='payment_state'),
        nullable=False,
        default='open'
    )

    __mapper_args__ = {
        'polymorphic_on': source
    }

    @hybrid_property
    def paid(self):
        """ Our states are essentially one paid and n unpaid states (indicating
        various ways in which the payment can end up being unpaid).

        So this boolean acts as coarse filter to divide payemnts into the
        two states that really matter.

        """
        return self.state == 'paid'

    @classmethod
    def register_link(cls, linked_class):
        cls.linked_classes.append(linked_class)


def reset_payment_class(cls):
    cls.linked_classes = []

    for attr in dir(cls):
        if not attr.startswith('linked_'):
            continue
        if not isinstance(getattr(cls, attr), InstrumentedAttribute):
            continue

        delattr(cls, attr)
        del cls.__mapper__._props[attr]

    return cls


@event.listens_for(mapper, 'before_configured')
def before_payment_instrumented():
    classes = [Payment]

    while classes:
        cls = reset_payment_class(classes.pop())
        classes.extend(cls.__subclasses__())
