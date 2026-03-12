from __future__ import annotations

import hmac
import hashlib
import morepath

from onegov.core.security import Public, Private, Secret
from onegov.form import Form
from onegov.org import _
from onegov.org.app import OrgApp
from onegov.org.layout import PaymentProviderLayout
from onegov.core.elements import Link, Confirm, Intercooler
from onegov.pay import Payment, PaymentCollection
from onegov.pay import PaymentProvider, PaymentProviderCollection
from onegov.pay.models.payment_providers import DatatransProvider
from onegov.pay.models.payment_providers import StripeConnect
from onegov.pay.models.payment_providers import WorldlineSaferpay
from purl import URL
from sqlalchemy.orm.attributes import flag_modified
from webob import Response
from webob.exc import HTTPBadRequest
from wtforms.fields import BooleanField, StringField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@OrgApp.html(
    model=PaymentProviderCollection,
    permission=Secret,
    template='payment_providers.pt'
)
def view_payment_providers(
    self: PaymentProviderCollection,
    request: OrgRequest,
    layout: PaymentProviderLayout | None = None
) -> RenderData:

    layout = layout or PaymentProviderLayout(self, request)

    def links(provider: PaymentProvider[Payment]) -> Iterator[Link]:
        if not provider.default and provider.enabled:
            yield Link(
                _('As default'),
                request.link(provider, 'default'),
                traits=(
                    Confirm(
                        _('Should this provider really be the new default?'),
                        _('All future payments will be redirected.'),
                        _('Make Default'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.link(self)
                    )
                )
            )

        yield Link(
            _('Settings'),
            request.link(provider, 'settings'),
        )

        if not provider.enabled:
            yield Link(
                _('Enable'),
                request.link(provider, 'enable'),
                traits=(
                    Confirm(
                        _('Should this provider really be enabled?'),
                        None,
                        _('Enable'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.link(self)
                    )
                )
            )
        else:
            yield Link(
                _('Disable'),
                request.link(provider, 'disable'),
                traits=(
                    Confirm(
                        _('Should this provider really be disabled?'),
                        None,
                        _('Disable'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.link(self)
                    )
                )
            )

        if not provider.payments:
            yield Link(
                _('Delete'),
                layout.csrf_protected_url(request.link(provider)),
                traits=(
                    Confirm(
                        _('Do you really want to delete this provider?'),
                        _('This cannot be undone.'),
                        _('Delete'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='DELETE',
                        target='#' + provider.id.hex,
                        redirect_after=request.link(self)
                    )
                )
            )

    return {
        'layout': layout,
        'links': links,
        'providers': tuple(self.query().order_by(PaymentProvider.created)),
        'title': _('Payment Provider'),
    }


@OrgApp.view(
    model=PaymentProviderCollection,
    name='stripe-connect-oauth',
    permission=Public
)
def new_stripe_connect_provider(
    self: PaymentProviderCollection,
    request: OrgRequest
) -> Response | None:

    # since the csrf token salt is different for unauthenticated requests
    # we need to specify a constant one here
    # this means that any user could in theory get this token and then bypass
    # our csrf protection. However that person would have to have an admin
    # account on the same physical server (which limits the attack-surface)
    salt = 'stripe-connect-oauth'

    provider = StripeConnect(
        **request.app.payment_provider_defaults['stripe_connect'])

    if request.is_admin and 'csrf-token' not in request.params:
        url_obj = URL(request.url)
        url_obj = url_obj.query_param(
            'csrf-token', request.new_csrf_token(salt=salt))
        handler_url = url_obj.as_string()

        org = request.app.org

        return morepath.redirect(provider.prepare_oauth_request(
            handler_url,
            success_url=request.link(self, 'stripe-connect-oauth-success'),
            error_url=request.link(self, 'stripe-connect-oauth-error'),
            user_fields={
                'email': org.reply_to,
                'url': request.link(org),
                'country': 'CH',
                'business_name': org.name,
                'currency': 'CHF'
            }
        ))

    # we got a response from stripe!
    request.assert_valid_csrf_token(salt=salt)
    provider.process_oauth_response(request.params)

    # it's possible to add the same payment twice, in which case we update the
    # data of the existing payment
    for other in self.query().filter_by(type=provider.type):
        if provider.identity == other.identity:
            other.meta = provider.meta
            other.content = provider.content
            return None

    # if this is the first account, it should be the default
    if not self.query().count():
        provider.default = True

    request.session.add(provider)
    return None


@OrgApp.view(
    model=PaymentProviderCollection,
    name='stripe-connect-oauth-success',
    permission=Secret
)
def new_stripe_connection_success(
    self: PaymentProviderCollection,
    request: OrgRequest
) -> Response:

    request.success(_('Your Stripe account was connected successfully.'))
    return morepath.redirect(request.link(self))


@OrgApp.view(
    model=PaymentProviderCollection,
    name='stripe-connect-oauth-error',
    permission=Secret
)
def new_stripe_connection_error(
    self: PaymentProviderCollection,
    request: OrgRequest
) -> Response:

    request.alert(_('Your Stripe account could not be connected.'))
    return morepath.redirect(request.link(self))


@OrgApp.view(
    model=PaymentProvider,
    name='default',
    permission=Secret,
    request_method='POST'
)
def handle_default_provider(
    self: PaymentProvider[Payment],
    request: OrgRequest
) -> None:

    providers = PaymentProviderCollection(request.session)
    providers.as_default(self)

    request.success(_('Changed the default payment provider.'))


@OrgApp.view(
    model=PaymentProvider,
    name='enable',
    permission=Secret,
    request_method='POST')
def enable_provider(
    self: PaymentProvider[Payment],
    request: OrgRequest
) -> None:

    self.enabled = True

    request.success(_('Provider enabled.'))


@OrgApp.view(
    model=PaymentProvider,
    name='disable',
    permission=Secret,
    request_method='POST')
def disable_provider(
    self: PaymentProvider[Payment],
    request: OrgRequest
) -> None:

    self.enabled = False

    request.success(_('Provider disabled.'))


@OrgApp.view(
    model=PaymentProvider,
    permission=Secret,
    request_method='DELETE'
)
def delete_provider(
    self: PaymentProvider[Payment],
    request: OrgRequest
) -> None:

    request.assert_valid_csrf_token()

    providers = PaymentProviderCollection(request.session)
    providers.delete(self)

    request.success(_('The payment provider was deleted.'))


@OrgApp.view(
    model=PaymentProviderCollection,
    name='sync',
    permission=Private
)
def sync_payments(
    self: PaymentProviderCollection,
    request: OrgRequest
) -> Response:

    self.sync()
    request.success(_('Successfully synchronised payments'))
    return request.redirect(request.class_link(PaymentCollection))


class DatatransSettingsForm(Form):
    merchant_name = StringField(
        label=_('Merchant Name'),
        validators=[InputRequired()],
    )
    merchant_id = StringField(
        label=_('UPP Username'),
        validators=[InputRequired()],
    )
    password = StringField(
        label=_('UPP Password'),
        validators=[InputRequired()],
    )
    webhook_key = StringField(
        label=_('Webhook Signing Key'),
    )
    charge_fee_to_customer = BooleanField(
        label=_('Charge fees to customer')
    )
    sandbox = BooleanField(
        label=_('Use sandbox environment (for testing)')
    )


class SaferpaySettingsForm(Form):
    customer_name = StringField(
        label=_('Customer Name'),
        validators=[InputRequired()],
    )
    customer_id = StringField(
        label=_('Customer ID'),
        validators=[InputRequired()],
    )
    terminal_id = StringField(
        label=_('Terminal ID'),
        validators=[InputRequired()],
    )
    api_username = StringField(
        label=_('API Username'),
    )
    api_password = StringField(
        label=_('API Password'),
    )
    charge_fee_to_customer = BooleanField(
        label=_('Charge fees to customer')
    )
    sandbox = BooleanField(
        label=_('Use sandbox environment (for testing)')
    )


def get_settings_form(
    model: PaymentProvider[Payment],
    request: OrgRequest
) -> type[Form]:

    if model.type == 'stripe_connect':
        class SettingsForm(Form):
            charge_fee_to_customer = BooleanField(
                label=_('Charge fees to customer')
            )
    elif model.type == 'datatrans':
        return DatatransSettingsForm
    elif model.type == 'worldline_saferpay':
        return SaferpaySettingsForm
    else:
        raise NotImplementedError

    return SettingsForm


@OrgApp.form(
    model=PaymentProvider,
    permission=Secret,
    form=get_settings_form,
    template='form.pt',
    name='settings'
)
def handle_provider_settings(
    self: PaymentProvider[Payment],
    request: OrgRequest,
    form: Form,
    layout: PaymentProviderLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        flag_modified(self, 'meta')

        request.success(_('Your changes were saved'))
        return request.redirect(request.class_link(PaymentProviderCollection))

    elif not request.POST:
        form.process(obj=self)

    layout = layout or PaymentProviderLayout(self, request)
    layout.breadcrumbs.append(Link(self.title, '#'))

    return {
        'layout': layout,
        'title': self.title,
        'lead': self.public_identity,
        'form': form
    }


@OrgApp.form(
    model=PaymentProviderCollection,
    permission=Secret,
    form=DatatransSettingsForm,
    template='form.pt',
    name='new-datatrans'
)
def handle_new_datatrans(
    self: PaymentProviderCollection,
    request: OrgRequest,
    form: DatatransSettingsForm,
    layout: PaymentProviderLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        provider = DatatransProvider()
        form.populate_obj(provider)
        self.session.add(provider)
        self.session.flush()

        request.success(_('Datatrans has been added'))
        return request.redirect(request.class_link(PaymentProviderCollection))

    title = _('Add Datatrans')
    layout = layout or PaymentProviderLayout(self, request)
    layout.breadcrumbs.append(Link(title, '#'))

    return {
        'layout': layout,
        'title': title,
        'form': form
    }


@OrgApp.form(
    model=PaymentProviderCollection,
    permission=Secret,
    form=SaferpaySettingsForm,
    template='form.pt',
    name='new-saferpay'
)
def handle_new_saferpay(
    self: PaymentProviderCollection,
    request: OrgRequest,
    form: SaferpaySettingsForm,
    layout: PaymentProviderLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        provider = WorldlineSaferpay()
        form.populate_obj(provider)
        self.session.add(provider)
        self.session.flush()

        request.success(_('Worldline Saferpay has been added'))
        return request.redirect(request.class_link(PaymentProviderCollection))

    title = _('Add Worldline Saferpay')
    layout = layout or PaymentProviderLayout(self, request)
    layout.breadcrumbs.append(Link(title, '#'))

    return {
        'layout': layout,
        'title': title,
        'form': form
    }


@OrgApp.view(
    model=DatatransProvider,
    permission=Secret,
    name='webhook',
    request_method='POST'
)
def handle_webhook(
    self: DatatransProvider,
    request: OrgRequest
) -> Response:

    if self.webhook_key:
        signature_header = request.headers.get('Datatrans-Signature')
        if signature_header is None:
            raise HTTPBadRequest()

        signature_params = dict(
            pair
            for part in signature_header.split(',')
            if len(pair := part.split('=')) == 2
        )
        timestamp = signature_params.get('t', '')
        try:
            signature = bytes.fromhex(signature_params.get('s0', ''))
        except Exception:
            signature = b''
        hmac_obj = hmac.new(
            bytes.fromhex(self.webhook_key),
            digestmod=hashlib.sha256
        )
        hmac_obj.update(timestamp.encode('utf-8'))
        hmac_obj.update(request.body)
        if not hmac.compare_digest(signature, hmac_obj.digest()):
            raise HTTPBadRequest()

    # NOTE: For now we don't do anything. If we wanted to be extra safe
    #       then we could keep a list of transaction ids we have received
    #       a webhook for in Redis, so only requests that contain one
    #       of those transaction ids will be able to proceed with payment
    #       We could also use this to cancel pending transactions, if
    #       they don't get settled within a certain time period.
    return Response()
