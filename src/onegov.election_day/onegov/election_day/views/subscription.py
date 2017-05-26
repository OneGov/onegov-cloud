from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.forms import SubscribeForm
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Principal
from onegov.election_day.collections import SubscriberCollection


@ElectionDayApp.form(model=Principal, name='subscribe',
                     template='form.pt', permission=Public, form=SubscribeForm)
def subscribe(self, request, form):
    layout = DefaultLayout(self, request)

    callout = None
    if form.submitted(request):
        subscribers = SubscriberCollection(request.app.session())
        subscribers.subscribe(form.formatted_phone_number, request.locale)
        callout = _(
            "Successfully subscribed to the SMS services. You will receive an "
            "SMS every time new results are published."
        )

    return {
        'layout': layout,
        'form': form,
        'title': _("Get SMS alerts"),
        'message': _(
            "You will receive an SMS as soon as new results have been "
            "published. The SMS service is free of charge. You can "
            "unsubscribe at any time."
        ),
        'cancel': layout.homepage_link,
        'callout': callout,
        'show_form': False if callout else True
    }


@ElectionDayApp.form(model=Principal, name='unsubscribe',
                     template='form.pt', permission=Public, form=SubscribeForm)
def unsubscribe(self, request, form):
    layout = DefaultLayout(self, request)

    callout = None
    if form.submitted(request):
        subscribers = SubscriberCollection(request.app.session())
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
