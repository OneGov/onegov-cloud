from __future__ import annotations

from onegov.core.security import Secret

from onegov.org.views.payment_provider import (
    view_payment_providers, get_settings_form, handle_provider_settings,
    handle_new_datatrans, DatatransSettingsForm, handle_new_saferpay,
    SaferpaySettingsForm)
from onegov.town6.app import TownApp
from onegov.pay import Payment, PaymentProvider, PaymentProviderCollection
from onegov.town6.layout import PaymentProviderLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=PaymentProviderCollection,
    permission=Secret,
    template='payment_providers.pt'
)
def town_view_payment_providers(
    self: PaymentProviderCollection,
    request: TownRequest
) -> RenderData:
    return view_payment_providers(
        self, request, PaymentProviderLayout(self, request))


@TownApp.form(
    model=PaymentProvider,
    permission=Secret,
    form=get_settings_form,
    template='form.pt',
    name='settings'
)
def town_handle_provider_settings(
    self: PaymentProvider[Payment],
    request: TownRequest,
    form: Form
) -> RenderData | Response:
    return handle_provider_settings(
        self, request, form, PaymentProviderLayout(self, request))


@TownApp.form(
    model=PaymentProviderCollection,
    permission=Secret,
    form=DatatransSettingsForm,
    template='form.pt',
    name='new-datatrans'
)
def town_handle_new_datatrans(
    self: PaymentProviderCollection,
    request: TownRequest,
    form: DatatransSettingsForm,
) -> RenderData | Response:
    return handle_new_datatrans(
        self, request, form, PaymentProviderLayout(self, request))


@TownApp.form(
    model=PaymentProviderCollection,
    permission=Secret,
    form=SaferpaySettingsForm,
    template='form.pt',
    name='new-saferpay'
)
def town_handle_new_saferpay(
    self: PaymentProviderCollection,
    request: TownRequest,
    form: SaferpaySettingsForm,
) -> RenderData | Response:
    return handle_new_saferpay(
        self, request, form, PaymentProviderLayout(self, request))
