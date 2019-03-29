from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.user import UserGroup
from onegov.wtfs.models.payment_type import PaymentType
from sqlalchemy.orm import object_session


class Municipality(UserGroup, TimestampMixin):
    """ A municipality / user group. """

    __mapper_args__ = {'polymorphic_identity': 'wtfs'}

    #: The name of the municipality.
    bfs_number = meta_property()

    #: The address supplement, used for invoices.
    address_supplement = meta_property()

    #: The GPN number, used for invoices.
    gpn_number = meta_property()

    #: The payment type. Typically normal (7.00) or special (8.50).
    payment_type = meta_property('payment_type')

    @property
    def price_per_quantity(self):
        if self.payment_type:
            query = object_session(self).query(PaymentType)
            query = query.filter_by(name=self.payment_type)
            payment_type = query.first()
            if payment_type:
                return payment_type.price_per_quantity or 0

        return 0

    @property
    def has_data(self):
        if self.pickup_dates.first() or self.scan_jobs.first():
            return True
        return False
