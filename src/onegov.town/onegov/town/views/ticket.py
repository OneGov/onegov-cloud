from onegov.core.security import Public
from onegov.ticket import Ticket
from onegov.town import _, TownApp
from onegov.town.layout import DefaultLayout


@TownApp.html(model=Ticket, name='status', template='ticket_status.pt',
              permission=Public)
def view_ticket_status(self, request):

    if self.state == 'open':
        title = _("Your request has been submitted")
    elif self.state == 'pending':
        title = _("Your request is currently pending")
    elif self.state == 'closed':
        title = _("Your request has been processed")
    else:
        raise NotImplementedError

    return {
        'title': title,
        'layout': DefaultLayout(self, request),
        'ticket': self
    }
