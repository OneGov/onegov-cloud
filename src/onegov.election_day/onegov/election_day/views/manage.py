""" The authentication views. """

from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import Layout
from onegov.election_day.models import Manage


@ElectionDayApp.html(model=Manage, template='manage.pt', permission=Private)
def view_manage(self, request):
    """ Shows the manage interface. """

    return {
        'layout': Layout(self, request),
        'title': _("Manage"),
        'votes': self.votes
    }
