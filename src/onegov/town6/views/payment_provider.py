from onegov.core.security import Secret

from onegov.org.views.payment_provider import view_payment_providers, \
    get_settings_form, handle_provider_settings
from onegov.town6.app import TownApp
from onegov.pay import PaymentProvider
from onegov.pay import PaymentProviderCollection
from onegov.town6.layout import PaymentProviderLayout


@TownApp.html(
    model=PaymentProviderCollection,
    permission=Secret,
    template='payment_providers.pt')
def town_view_payment_providers(self, request):
    return view_payment_providers(
        self, request, PaymentProviderLayout(self, request))


@TownApp.form(
    model=PaymentProvider,
    permission=Secret,
    form=get_settings_form,
    template='form.pt',
    name='settings')
def town_handle_provider_settings(self, request, form):
    return handle_provider_settings(
        self, request, form, PaymentProviderLayout(self, request))
