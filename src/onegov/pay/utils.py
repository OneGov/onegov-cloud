from collections import namedtuple
from decimal import Decimal
from functools import total_ordering
from onegov.core.orm import Base


@total_ordering
class Price(namedtuple('PriceBase', (
    'amount', 'currency', 'fee', 'credit_card_payment'
))):
    """ A single price.

    The amount includes the fee. To get the net amount use the net_amount
    property.

    """

    def __new__(cls, amount, currency, fee=0, credit_card_payment=False):
        return super().__new__(
            cls,
            Decimal(amount),
            currency,
            Decimal(fee),
            credit_card_payment
        )

    def __bool__(self):
        return self.amount and True or False

    def __lt__(self, other):
        # FIXME: This probably should assert equal currency as well
        return self.amount < other.amount

    def __add__(self, other):
        assert self.currency is None or self.currency == other.currency
        cc_payment = self.credit_card_payment or other.credit_card_payment
        return self.__class__(
            self.amount + other.amount,
            self.currency or other.currency,
            credit_card_payment=cc_payment
        )

    def __sub__(self, other):
        assert self.currency == other.currency
        cc_payment = self.credit_card_payment or other.credit_card_payment
        return self.__class__(
            self.amount - other.amount,
            self.currency,
            credit_card_payment=cc_payment
        )

    def __str__(self):
        return '{:.2f} {}'.format(self.amount, self.currency)

    def __repr__(self):
        return 'Price({}, {})'.format(repr(self.amount), repr(self.currency))

    @classmethod
    def zero(cls):
        return cls(0, None)

    def as_dict(self):
        return {
            'amount': float(self.amount),
            'currency': self.currency,
            'fee': float(self.fee),
            'credit_card_payment': self.credit_card_payment
        }

    @property
    def net_amount(self):
        return self.amount - self.fee


def payments_association_table_for(cls):
    return Base.metadata.tables[f'payments_for_{cls.__tablename__}_payments']
