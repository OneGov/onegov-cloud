from more.webassets import WebassetsApp
from onegov.core.orm import orm_cached
from onegov.pay import PaymentProvider


class PayApp(WebassetsApp):
    """ Provides payment integration for
    :class:`onegov.core.framework.Framework` based applications.

    """

    def configure_payment_providers(self, **cfg):
        """ Configures the preconfigured parameters for payment providers.

        Takes one dictionary for each availble provider. Available providers
        can be found in the models/payment_providers folder. For example::

            payment_provider_defaults:
                stripe_connect:
                    client_id: foo
                    client_secret: bar

        Since multiple payment providers (even of the same type) may exist,
        and because some information stored on the payment providers need
        to be configured differently for each application_id (and possibly
        set up through OAuth) we only provide default parameters.

        When we create a new payment provider, these default values may be
        read by the payment provider.

        """

        self.payment_provider_defaults = cfg.get(
            'payment_provider_defaults', {})

    @orm_cached(policy='on-table-change:payment_providers')
    def default_payment_provider(self):
        return self.session().query(PaymentProvider)\
            .filter_by(default=True).first()


@PayApp.webasset_path()
def get_js_path():
    return 'assets/js'


@PayApp.webasset('pay')
def get_pay_assets():
    yield 'stripe.js'
