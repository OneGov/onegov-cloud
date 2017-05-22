""" The manage subscription views. """

import morepath

from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.forms import DeleteForm
from onegov.election_day.layout import ManageSubscribersLayout
from onegov.election_day.models import Subscriber


@ElectionDayApp.html(model=SubscriberCollection,
                     template='manage/subsribers.pt',
                     permission=Private)
def view_subscribers(self, request):

    return {
        'layout': ManageSubscribersLayout(self, request),
        'title': _("Manage"),
        'count': self.query().count(),
        'subscribers': self.batch,
        'term': self.term
    }


@ElectionDayApp.form(model=Subscriber, name='delete', template='form.pt',
                     permission=Private, form=DeleteForm)
def delete_subscriber(self, request, form):

    layout = ManageSubscribersLayout(self, request)

    if form.submitted(request):
        subscribers = SubscriberCollection(request.app.session())
        subscribers.unsubscribe(self.phone_number)
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
