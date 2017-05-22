import stripe

from onegov.pay.models.payment_provider import PaymentProvider
from onegov.core.orm.mixins import meta_property


# We use pycurl because it's faster and more robust than anything else
stripe.default_http_client = stripe.http_client.PycurlClient()


class StripeConnect(PaymentProvider):

    __mapper_args__ = {'polymorphic_identity': 'stripe_connect'}

    #: The Stripe Connect client id
    client_id = meta_property('client_id')

    #: The API key of the connect user
    client_secret = meta_property('client_secret')

    #: The authorization code provided by OAuth
    authorization_code = meta_property('authorization_code')

    #: The public stripe key
    publishable_key = meta_property('publishable_key')

    #: The stripe user id as confirmed by OAuth
    user_id = meta_property('user_id')

    #: The refresh token provided by OAuth
    refresh_token = meta_property('refresh_token')

    #: The access token provieded by OAuth
    access_token = meta_property('access_token')

    @property
    def title(self):
        return 'Stripe Connect'

    @property
    def identity(self):
        return self.publishable_key

    def params(self, **p):
        assert self.client_id and self.client_secret

        p.setdefault('client_id', self.client_id)
        p.setdefault('client_secret', self.access_token or self.client_secret)

        return p

    def oauth_url(self, redirect_uri, user_fields=None):
        """ Generates an oauth url to be shown in the browser. """

        return stripe.OAuth.authorize_url(
            **self.params(
                scope='read_write',
                redirect_uri=redirect_uri,
                stripe_user=user_fields
            )
        )

    def process_oauth_response(self, request_params):
        """ Takes the parameters of an incoming oauth request and stores
        them on the payment provider if successful.

        """

        if 'error' in request_params:
            raise RuntimeError("Stripe OAuth request failed ({}: {})".format(
                request_params['error'], request_params['error_description']
            ))

        self.authorization_code = request_params['code']

        token = stripe.OAuth.token(
            **self.params(
                grant_type='authorization_code',
                code=self.authorization_code,
            )
        )

        assert token['scope'] == 'read_write'

        self.publishable_key = token['stripe_publishable_key']
        self.user_id = token['stripe_user_id']
        self.refresh_token = token['refresh_token']
        self.access_token = token['access_token']
