from onegov.core.i18n import SiteLocale
from onegov.core.security import Public
from onegov.org import OrgApp


@OrgApp.view(model=SiteLocale, permission=Public)
def change_site_locale(self, request):
    return self.redirect()
