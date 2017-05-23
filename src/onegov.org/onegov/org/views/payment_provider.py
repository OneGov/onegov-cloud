import morepath

from onegov.core.security import Public, Secret
from onegov.org import _
from onegov.org.app import OrgApp
from onegov.org.layout import PaymentProviderLayout
from onegov.pay import PaymentProviderCollection
from onegov.pay.models.payment_providers import StripeConnect
from purl import URL


@OrgApp.html(
    model=PaymentProviderCollection,
    permission=Secret,
    template='payment_providers.pt')
def view_payment_providers(self, request):
    return {
        'providers': tuple(self.query()),
        'layout': PaymentProviderLayout(self, request),
        'title': _("Payment Provider")
    }


@OrgApp.view(
    model=PaymentProviderCollection,
    name='stripe-connect-oauth',
    permission=Public)
def new_stripe_connect_provider(self, request):

    payment = StripeConnect(
        **request.app.payment_provider_defaults['stripe_connect'])

    if request.is_admin and 'csrf-token' not in request.params:
        handler = URL(request.url)
        handler = handler.query_param('csrf-token', request.new_csrf_token())
        handler = handler.as_string()

        org = request.app.org

        return morepath.redirect(payment.prepare_oauth_request(handler, {
            'email': org.reply_to,
            'url': request.link(org),
            'country': 'CH',
            'business_name': org.name,
            'currency': 'CHF'
        }))

    # we got a response from stripe!
    request.assert_valid_csrf_token()
    payment.process_oauth_response(request.params)

    # if this is the first account, it should be the default
    if not self.query().count():
        payment.default = True

    request.app.session().add(payment)
    request.success(_("Your Stripe account was connected successfully."))
