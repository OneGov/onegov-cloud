from onegov.core.orm.abstract import associated
from onegov.pay.models.payment import Payment


class Payable(object):
    """ Links the parent model with 0 to n :class:`~onegov.pay.models.Payment`
    records through an automatically generated association table.

    """

    payment = associated(Payment, 'payment', 'many-to-many', uselist=False)
