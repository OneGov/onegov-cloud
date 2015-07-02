from onegov.core.security import Public
from onegov.org import Organization
from onegov.town import TownApp
from onegov.town.layout import OrganizationLayout


@TownApp.html(model=Organization, template='organization.pt',
              permission=Public)
def view_organization(self, request):
    return {
        'title': self.title,
        'organization': self,
        'layout': OrganizationLayout(self, request)
    }
