from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.user import UserGroup
from onegov.wtfs.models.payment_type import PaymentType
from sqlalchemy.orm import object_session


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm.mixins import dict_property
    from onegov.core.types import AppenderQuery
    from onegov.wtfs.models import PickupDate, ScanJob
    from sqlalchemy.orm import relationship


class Municipality(UserGroup, TimestampMixin):
    """ A municipality / user group. """

    __mapper_args__ = {'polymorphic_identity': 'wtfs'}

    #: The name of the municipality.
    bfs_number: 'dict_property[int]' = meta_property()

    #: The address supplement, used for invoices.
    address_supplement: 'dict_property[str]' = meta_property()

    #: The GPN number, used for invoices.
    gpn_number: 'dict_property[int]' = meta_property()

    #: The payment type. Typically normal (7.00) or special (8.50).
    payment_type: 'dict_property[str]' = meta_property('payment_type')

    if TYPE_CHECKING:
        # forward declare backrefs
        pickup_dates: relationship[AppenderQuery[PickupDate]]
        scan_jobs: relationship[AppenderQuery[ScanJob]]

    @property
    def price_per_quantity(self) -> int:
        if self.payment_type:
            query = object_session(self).query(PaymentType)
            query = query.filter_by(name=self.payment_type)
            payment_type = query.first()
            if payment_type:
                return payment_type.price_per_quantity or 0

        return 0

    @property
    def has_data(self) -> bool:
        # FIXME: It might be faster to do an exists() query, but that depends
        #        on how AppenderQuery interacts with `back_populates`
        if self.pickup_dates.first() or self.scan_jobs.first():
            return True
        return False

    @property
    def contacts(self) -> list[str]:
        return [
            user.username for user in self.users
            if (user.data or {}).get('contact', False)
        ]
