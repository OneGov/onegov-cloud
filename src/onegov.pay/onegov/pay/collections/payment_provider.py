from onegov.core.collection import GenericCollection
from onegov.pay.models import PaymentProvider


class PaymentProviderCollection(GenericCollection):
    """ Manages the payment providers. """

    @property
    def model_class(self):
        return PaymentProvider
