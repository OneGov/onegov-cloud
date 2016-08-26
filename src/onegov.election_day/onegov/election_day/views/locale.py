from onegov.core.i18n import SiteLocale
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp


@ElectionDayApp.view(model=SiteLocale, permission=Public)
def change_site_locale(self, request):
    return self.redirect()
