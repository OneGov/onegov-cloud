from onegov.core.collection import GenericCollection
from onegov.wtfs.models import PaymentType


class PaymentTypeCollection(GenericCollection):

    @property
    def model_class(self):
        return PaymentType
