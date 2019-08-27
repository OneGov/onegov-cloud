from onegov.core.security import Public
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org.models import AtoZ


@OrgApp.html(model=AtoZ, template='atoz.pt', permission=Public)
def atoz(self, request):

    layout = DefaultLayout(self, request)
    layout.breadcrumbs.append(Link(_("Topics A-Z"), '#'))

    return {
        'title': _("Topics A-Z"),
        'model': self,
        'layout': layout
    }
