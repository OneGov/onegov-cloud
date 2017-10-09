from onegov.core.orm.abstract import associated
from onegov.pay.models.payment import Payment


class Payable(object):
    """ Links the parent model with 0 to n :class:`~onegov.pay.models.Payment`
    records through an automatically generated association table.

    """

    payment = associated(Payment, 'payment', 'many-to-many', uselist=False)


class PayableManyTimes(object):
    """ Same as :class:`Payable`, but using a list of payments instead of
    a single one (proper many-to-many payments).

    """

    payments = associated(Payment, 'payments', 'many-to-many', uselist=True)
