from onegov.core.collection import GenericCollection
from onegov.wtfs.models import PaymentType


class PaymentTypeCollection(GenericCollection[PaymentType]):

    @property
    def model_class(self) -> type[PaymentType]:
        return PaymentType
