from onegov.core.orm.mixins import TimestampMixin
from onegov.user import UserGroup
from onegov.core.orm.mixins import meta_property


class Municipality(UserGroup, TimestampMixin):
    """ A municipality / user group. """

    __mapper_args__ = {'polymorphic_identity': 'wtfs'}

    #: The name of the municipality.
    bfs_number = meta_property()

    #: The address supplement, used for invoices.
    address_supplement = meta_property()

    #: The GPN number, used for invoices.
    gpn_number = meta_property()

    #: The price per quantity times hundred, used for invoices. Typically
    #: 700 (normal) or 850 (special).
    _price_per_quantity = meta_property(default=700)

    @property
    def price_per_quantity(self):
        return (self._price_per_quantity or 0) / 100

    @price_per_quantity.setter
    def price_per_quantity(self, value):
        self._price_per_quantity = (value or 0) * 100

    @property
    def has_data(self):
        if self.pickup_dates.first() or self.scan_jobs.first():
            return True
        return False
