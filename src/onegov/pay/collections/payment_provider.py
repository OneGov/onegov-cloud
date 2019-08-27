from onegov.core.collection import GenericCollection
from onegov.pay.models import PaymentProvider


class PaymentProviderCollection(GenericCollection):
    """ Manages the payment providers. """

    @property
    def model_class(self):
        return PaymentProvider

    def as_default(self, provider):
        for other in self.query():
            other.default = False

        self.session.flush()
        provider.default = True

    def sync(self):
        """ Syncs all payments with the related payment providers.

        """

        for provider in self.query():
            provider.sync()
