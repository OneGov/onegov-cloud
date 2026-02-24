from __future__ import annotations

from onegov.core.i18n import SiteLocale
from onegov.core.security import Public
from onegov.swissvotes import SwissvotesApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.request import SwissvotesRequest
    from webob import Response


@SwissvotesApp.view(
    model=SiteLocale,
    permission=Public
)
def change_site_locale(
    self: SiteLocale,
    request: SwissvotesRequest
) -> Response:
    """ Changes the locale. """

    return self.redirect(request)
