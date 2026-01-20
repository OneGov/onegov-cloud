from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.pay.models import PaymentProvider


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pay.models import Payment


class PaymentProviderCollection(GenericCollection[PaymentProvider['Payment']]):
    """ Manages the payment providers. """

    @property
    def model_class(self) -> type[PaymentProvider[Payment]]:
        return PaymentProvider

    def as_default(self, provider: PaymentProvider[Any]) -> None:
        for other in self.query():
            other.default = False

        self.session.flush()
        provider.default = True

    def sync(self) -> None:
        """ Syncs all payments with the related payment providers.

        """

        for provider in self.query():
            provider.sync()
