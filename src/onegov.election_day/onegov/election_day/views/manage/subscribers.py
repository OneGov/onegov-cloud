""" The manage subscription views. """

import morepath

from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.layout import ManageSubscribersLayout
from onegov.election_day.models import Subscriber


@ElectionDayApp.manage_html(
    model=SubscriberCollection,
    template='manage/subsribers.pt'
)
def view_subscribers(self, request):

    """ View a list with all subscribers. """

    return {
        'layout': ManageSubscribersLayout(self, request),
        'title': _("Subscribers"),
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
        subscribers = SubscriberCollection(request.app.session())
        subscribers.unsubscribe(self.phone_number)
        request.message(_("Subscriber deleted."), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={
                'item': self.phone_number
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.phone_number,
        'subtitle': _("Delete subscriber"),
        'button_text': _("Delete subscriber"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }
