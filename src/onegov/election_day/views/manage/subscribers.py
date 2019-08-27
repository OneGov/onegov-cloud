from morepath import redirect
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.layouts import ManageSubscribersLayout
from onegov.election_day.models import Subscriber


@ElectionDayApp.manage_html(
    model=SmsSubscriberCollection,
    template='manage/subscribers.pt'
)
def view_sms_subscribers(self, request):

    """ View a list with all SMS subscribers. """

    return {
        'layout': ManageSubscribersLayout(self, request),
        'title': _("SMS subscribers"),
        'address_title': _("Phone number"),
        'count': self.query().count(),
        'subscribers': self.batch,
        'term': self.term
    }


@ElectionDayApp.manage_html(
    model=EmailSubscriberCollection,
    template='manage/subscribers.pt'
)
def view_email_subscribers(self, request):

    """ View a list with all email subscribers. """

    return {
        'layout': ManageSubscribersLayout(self, request),
        'title': _("Email subscribers"),
        'address_title': _("Email"),
        'count': self.query().count(),
        'subscribers': self.batch,
        'term': self.term
    }


@ElectionDayApp.manage_form(
    model=Subscriber,
    name='delete'
)
def delete_subscriber(self, request, form):

    """ Delete a single subsriber. """

    layout = ManageSubscribersLayout(self, request)

    if form.submitted(request):
        subscribers = SubscriberCollection(request.session)
        subscribers.unsubscribe(self.address)
        request.message(_("Subscriber deleted."), 'success')
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={
                'item': self.address
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.address,
        'subtitle': _("Delete subscriber"),
        'button_text': _("Delete subscriber"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }
