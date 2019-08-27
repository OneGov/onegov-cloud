from onegov.core.security import Public
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.models import Principal


@SwissvotesApp.html(
    model=Principal,
    template='home.pt',
    permission=Public
)
def view_home(self, request):
    """ The home page. """

    page = TranslatablePageCollection(request.session).setdefault('home')
    return request.redirect(request.link(page))
