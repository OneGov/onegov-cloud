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
    """ Adds the given email address to the email subscribers."""

    layout = DefaultLayout(self, request)

    callout = None
    if form.submitted(request):
        subscribers = EmailSubscriberCollection(request.session)
        subscribers.subscribe(form.email.data, request)
        callout = _(
            "Successfully subscribed to the email service. You will receive "
            "an email every time new results are published."
        )

    return {
        'layout': layout,
        'form': form,
        'title': _("Get email alerts"),
        'message': _(
            "You will receive an email as soon as new results have been "
            "published. You can unsubscribe at any time."
        ),
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': False if callout else True
    }


@ElectionDayApp.form(
    model=Principal,
    name='unsubscribe-email',
    template='form.pt',
    form=EmailSubscriptionForm,
    permission=Public
)
def unsubscribe_email(self, request, form):
    """ Removes the email number from the email subscribers.

    Allows one-click unsubscription as defined by RFC-8058:
        curl -X POST http://localhost:8080/xx/zg/unsubscribe-oneclick?opaque=yy

    """

    layout = DefaultLayout(self, request)
    subscribers = EmailSubscriberCollection(request.session)

    token = request.params.get('opaque', None)
    if request.method == 'POST' and token:
        data = request.load_url_safe_token(token) or {}
        subscribers.unsubscribe(data.get('address', None))
        return Response()

    callout = None
    if form.submitted(request):
        subscribers.unsubscribe(form.email.data)
        callout = _(
            "Successfully unsubscribed from the email services. You will no "
            "longer receive an email when new results are published."
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
        subscribers.subscribe(form.formatted_phone_number, request)
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
        subscribers.unsubscribe(form.formatted_phone_number)
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
