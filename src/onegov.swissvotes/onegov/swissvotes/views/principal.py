from onegov.core.security import Public
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.layouts import DefaultLayout
from onegov.swissvotes.models import Principal


@SwissvotesApp.html(
    model=Principal,
    template='home.pt',
    permission=Public
)
def view_home(self, request):
    """ The home page. """

    page = TranslatablePageCollection(request.session).by_id('home')
    if page:
        return request.redirect(request.link(page))

    return {
        'layout': DefaultLayout(self, request),
    }
