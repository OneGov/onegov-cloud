from onegov.core.i18n import SiteLocale
from onegov.core.security import Public
from onegov.swissvotes import SwissvotesApp


@SwissvotesApp.view(
    model=SiteLocale,
    permission=Public
)
def change_site_locale(self, request):
    """ Changes the locale. """

    return self.redirect()
