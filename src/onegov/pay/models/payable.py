import hashlib

from onegov.core.orm.abstract import associated
from onegov.pay.models.payment import Payment
from sqlalchemy import inspect


def hash_primary_key(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


class PayableBase(object):

    @property
    def payable_reference(self):
        """ A string which identifies this payable in payment lists. Do not
        join any values here as it can lead to an explosion of executed
        queries!

        By default we use the table name plus a hash derived from the
        primary key values of the table. This ensures that we do not
        accidentally leak secrets.

        In practice, this reference should be customised for each payable.

        """

        tablename = self.__tablename__

        keys = inspect(self.__class__).primary_key
        values = '/'.join((str(getattr(self, key.name, None)) for key in keys))

        return f'{tablename}/{hash_primary_key(values)}'


class Payable(PayableBase):
    """ Links the parent model with 0 to n :class:`~onegov.pay.models.Payment`
    records through an automatically generated association table.

    """

    payment = associated(Payment, 'payment', 'many-to-many', uselist=False)


class PayableManyTimes(PayableBase):
    """ Same as :class:`Payable`, but using a list of payments instead of
    a single one (proper many-to-many payments).

    """

    payments = associated(Payment, 'payments', 'many-to-many', uselist=True)
