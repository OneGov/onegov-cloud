from morepath.request import Response
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.forms import EmailSubscriptionForm
from onegov.election_day.forms import SmsSubscriptionForm
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal


@ElectionDayApp.form(
    model=Principal,
    name='subscribe-email',
    template='form.pt',
    form=EmailSubscriptionForm,
    permission=Public
)
def subscribe_email(self, request, form):
    """ Initiate the email notification subscription. """

    layout = DefaultLayout(self, request)
    message = _(
        "You will receive an email as soon as new results have been "
        "published. You can unsubscribe at any time."
    )
    callout = None
    if form.submitted(request):
        subscribers = EmailSubscriberCollection(request.session)
        subscribers.initiate_subscription(form.email.data, request)
        callout = _(
            "You will shortly receive an email to confirm your email."
        )
        message = ''

    return {
        'layout': layout,
        'form': form,
        'title': _("Get email alerts"),
        'message': message,
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': False if callout else True
    }


@ElectionDayApp.form(
    model=Principal,
    name='optin-email',
    template='form.pt',
    form=EmailSubscriptionForm,
    permission=Public
)
def optin_email(self, request, form):

    """ Confirm the email used for the subscription. """

    callout = _("Subscription failed, the link is invalid.")
    try:
        data = request.params.get('opaque')
        data = request.load_url_safe_token(data)
        address = data['address']
        locale = data['locale']
        assert address
        assert locale
    except Exception:
        pass
    else:
        subscribers = EmailSubscriberCollection(request.session)
        if subscribers.confirm_subscription(address, locale):
            callout = _(
                "Successfully subscribed to the email service. You will "
                "receive an email every time new results are published."
            )

    return {
        'layout': DefaultLayout(self, request),
        'form': form,
        'title': _("Get email alerts"),
        'callout': callout,
        'show_form': False
    }


@ElectionDayApp.form(
    model=Principal,
    name='unsubscribe-email',
    template='form.pt',
    form=EmailSubscriptionForm,
    permission=Public
)
def unsubscribe_email(self, request, form):
    """ Initiates the email notification unsubscription. """

    layout = DefaultLayout(self, request)
    callout = None
    if form.submitted(request):
        subscribers = EmailSubscriberCollection(request.session)
        subscribers.initiate_unsubscription(form.email.data, request)
        callout = _(
            "You will shortly receive an email to confirm your unsubscription."
        )

    return {
        'layout': layout,
        'form': form,
        'title': _("Stop email subscription"),
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': False if callout else True
    }


@ElectionDayApp.form(
    model=Principal,
    name='optout-email',
    template='form.pt',
    form=EmailSubscriptionForm,
    permission=Public
)
def optout_email(self, request, form):
    """ Deactivates the email subscription.

    Allows one-click unsubscription as defined by RFC-8058:
        curl -X POST http://localhost:8080/xx/zg/unsubscribe-email?opaque=yy

    """

    callout = _("Unsubscription failed, the link is invalid.")
    try:
        data = request.params.get('opaque')
        data = request.load_url_safe_token(data)
        address = data['address']
        assert address
    except Exception:
        pass
    else:
        subscribers = EmailSubscriberCollection(request.session)
        result = subscribers.confirm_unsubscription(address)
        if request.method == 'POST':
            # one-click unsubscribe
            return Response()
        if result:
            callout = _(
                "Successfully unsubscribed from the email services. You will "
                "no longer receive an email when new results are published."
            )

    return {
        'layout': DefaultLayout(self, request),
        'form': form,
        'title': _("Stop email subscription"),
        'callout': callout,
        'show_form': False
    }


@ElectionDayApp.form(
    model=Principal,
    name='subscribe-sms',
    template='form.pt',
    form=SmsSubscriptionForm,
    permission=Public
)
def subscribe_sms(self, request, form):
    """ Adds the given phone number to the SMS subscribers."""

    layout = DefaultLayout(self, request)

    callout = None
    if form.submitted(request):
        subscribers = SmsSubscriberCollection(request.session)
        subscribers.initiate_subscription(
            form.phone_number.formatted_data,
            request
        )
        callout = _(
            "Successfully subscribed to the SMS service. You will receive a "
            "SMS every time new results are published."
        )

    return {
        'layout': layout,
        'form': form,
        'title': _("Get SMS alerts"),
        'message': _(
            "You will receive a SMS as soon as new results have been "
            "published. The SMS service is free of charge. You can "
            "unsubscribe at any time."
        ),
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': False if callout else True
    }


@ElectionDayApp.form(
    model=Principal,
    name='unsubscribe-sms',
    template='form.pt',
    form=SmsSubscriptionForm,
    permission=Public
)
def unsubscribe_sms(self, request, form):
    """ Removes the given phone number from the SMS subscribers."""

    layout = DefaultLayout(self, request)

    callout = None
    if form.submitted(request):
        subscribers = SmsSubscriberCollection(request.session)
        subscribers.initiate_unsubscription(
            form.phone_number.formatted_data,
            request
        )
        callout = _(
            "Successfully unsubscribed from the SMS services. You will no "
            "longer receive SMS when new results are published."
        )

    return {
        'layout': layout,
        'form': form,
        'title': _("Stop SMS subscription"),
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': False if callout else True
    }
