from onegov.core.security import Public
from onegov.town import _, TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from onegov.town.models import AtoZ


@TownApp.html(model=AtoZ, template='atoz.pt', permission=Public)
def atoz(self, request):

    layout = DefaultLayout(self, request)
    layout.breadcrumbs.append(Link(_("Catalog A-Z"), '#'))

    return {
        'title': _("Catalog A-Z"),
        'model': self,
        'layout': layout
    }
