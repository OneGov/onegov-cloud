from __future__ import annotations

from morepath.request import Response
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day import log
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.forms import EmailSubscriptionForm
from onegov.election_day.forms import SmsSubscriptionForm
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal
from onegov.election_day.security import MaybePublic


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest


@ElectionDayApp.form(
    model=Principal,
    name='subscribe-email',
    template='form.pt',
    form=EmailSubscriptionForm,
    permission=MaybePublic
)
def subscribe_email(
    self: Principal,
    request: ElectionDayRequest,
    form: EmailSubscriptionForm
) -> RenderData:
    """ Initiate the email notification subscription. """

    layout = DefaultLayout(self, request)
    message: str = _(
        'You will receive an email as soon as new results have been '
        'published. You can unsubscribe at any time.'
    )
    callout = None
    if form.submitted(request):
        assert form.email.data is not None
        subscribers = EmailSubscriberCollection(request.session)
        subscribers.initiate_subscription(
            form.email.data,
            form.domain.data if form.domain else None,
            form.domain_segment.data if form.domain_segment else None,
            request
        )
        callout = _(
            'You will shortly receive an email to confirm your email.'
        )
        message = ''

    return {
        'layout': layout,
        'form': form,
        'title': _('Get email alerts'),
        'message': message,
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': not callout
    }


@ElectionDayApp.form(
    model=Principal,
    name='optin-email',
    template='form.pt',
    form=EmailSubscriptionForm,
    permission=MaybePublic
)
def optin_email(
    self: Principal,
    request: ElectionDayRequest,
    form: EmailSubscriptionForm
) -> RenderData:
    """ Confirm the email used for the subscription. """

    callout = _('Subscription failed, the link is invalid.')
    try:
        raw_data = request.params.get('opaque')
        assert isinstance(raw_data, str)
        data = request.load_url_safe_token(raw_data)
        assert data is not None
        address = data['address']
        locale = data['locale']
        domain = data.get('domain')
        domain_segment = data.get('domain_segment')
        assert address
        assert locale
    except Exception:
        log.warning('Invalid email optin')
    else:
        subscribers = EmailSubscriberCollection(request.session)
        result = subscribers.confirm_subscription(
            address, domain, domain_segment, locale
        )
        if result:
            callout = _(
                'Successfully subscribed to the email service. You will '
                'receive an email every time new results are published.'
            )

    return {
        'layout': DefaultLayout(self, request),
        'form': form,
        'title': _('Get email alerts'),
        'callout': callout,
        'show_form': False
    }


@ElectionDayApp.form(
    model=Principal,
    name='unsubscribe-email',
    template='form.pt',
    form=EmailSubscriptionForm,
    permission=MaybePublic
)
def unsubscribe_email(
    self: Principal,
    request: ElectionDayRequest,
    form: EmailSubscriptionForm
) -> RenderData:
    """ Initiates the email notification unsubscription. """

    layout = DefaultLayout(self, request)
    callout = None
    if form.submitted(request):
        assert form.email.data is not None
        subscribers = EmailSubscriberCollection(request.session)
        subscribers.initiate_unsubscription(
            form.email.data,
            form.domain.data if form.domain else None,
            form.domain_segment.data if form.domain_segment else None,
            request
        )
        callout = _(
            'You will shortly receive an email to confirm your unsubscription.'
        )

    return {
        'layout': layout,
        'form': form,
        'title': _('Stop email subscription'),
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': not callout
    }


@ElectionDayApp.form(
    model=Principal,
    name='optout-email',
    template='form.pt',
    form=EmailSubscriptionForm,
    permission=MaybePublic
)
def optout_email(
    self: Principal,
    request: ElectionDayRequest,
    form: EmailSubscriptionForm
) -> RenderData | Response:
    """ Deactivates the email subscription.

    Allows one-click unsubscription as defined by RFC-8058:
        curl -X POST http://localhost:8080/xx/zg/unsubscribe-email?opaque=yy

    """

    callout = _('Unsubscription failed, the link is invalid.')
    try:
        raw_data = request.params.get('opaque')
        assert isinstance(raw_data, str)
        data = request.load_url_safe_token(raw_data)
        assert data is not None
        address = data['address']
        domain = data.get('domain')
        domain_segment = data.get('domain_segment')
        assert address
    except Exception:
        log.warning('Invalid email optout')
    else:
        subscribers = EmailSubscriberCollection(request.session)
        result = subscribers.confirm_unsubscription(
            address, domain, domain_segment
        )
        if request.method == 'POST':
            # one-click unsubscribe
            return Response()
        if result:
            callout = _(
                'Successfully unsubscribed from the email services. You will '
                'no longer receive an email when new results are published.'
            )

    return {
        'layout': DefaultLayout(self, request),
        'form': form,
        'title': _('Stop email subscription'),
        'callout': callout,
        'show_form': False
    }


@ElectionDayApp.form(
    model=Principal,
    name='subscribe-sms',
    template='form.pt',
    form=SmsSubscriptionForm,
    permission=MaybePublic
)
def subscribe_sms(
    self: Principal,
    request: ElectionDayRequest,
    form: SmsSubscriptionForm
) -> RenderData:
    """ Adds the given phone number to the SMS subscribers."""

    layout = DefaultLayout(self, request)

    callout = None
    if form.submitted(request):
        phone_number = form.phone_number.formatted_data
        assert phone_number is not None
        subscribers = SmsSubscriberCollection(request.session)
        subscribers.initiate_subscription(
            phone_number,
            form.domain.data if form.domain else None,
            form.domain_segment.data if form.domain_segment else None,
            request
        )
        callout = _(
            'Successfully subscribed to the SMS service. You will receive a '
            'SMS every time new results are published.'
        )

    return {
        'layout': layout,
        'form': form,
        'title': _('Get SMS alerts'),
        'message': _(
            'You will receive a SMS as soon as new results have been '
            'published. The SMS service is free of charge. You can '
            'unsubscribe at any time.'
        ),
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': not callout
    }


@ElectionDayApp.form(
    model=Principal,
    name='unsubscribe-sms',
    template='form.pt',
    form=SmsSubscriptionForm,
    permission=MaybePublic
)
def unsubscribe_sms(
    self: Principal,
    request: ElectionDayRequest,
    form: SmsSubscriptionForm
) -> RenderData:
    """ Removes the given phone number from the SMS subscribers."""

    layout = DefaultLayout(self, request)

    callout = None
    if form.submitted(request):
        phone_number = form.phone_number.formatted_data
        assert phone_number is not None
        subscribers = SmsSubscriberCollection(request.session)
        subscribers.initiate_unsubscription(
            phone_number,
            form.domain.data if form.domain else None,
            form.domain_segment.data if form.domain_segment else None,
            request
        )
        callout = _(
            'Successfully unsubscribed from the SMS services. You will no '
            'longer receive SMS when new results are published.'
        )

    return {
        'layout': layout,
        'form': form,
        'title': _('Stop SMS subscription'),
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': not callout
    }
