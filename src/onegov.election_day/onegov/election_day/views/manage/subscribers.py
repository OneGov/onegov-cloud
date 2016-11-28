""" The manage subscription views. """

from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.layout import ManageLayout


@ElectionDayApp.html(model=SubscriberCollection,
                     template='manage_subsribers.pt',
                     permission=Private)
def view_subscribers(self, request):

    return {
        'layout': ManageLayout(self, request),
        'title': _("Manage"),
        'count': self.query().count(),
        'subscribers': self.query().all()
    }
