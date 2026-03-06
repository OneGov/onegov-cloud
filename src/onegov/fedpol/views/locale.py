from __future__ import annotations

from onegov.core.i18n import SiteLocale
from onegov.core.security import Public
from onegov.fedpol import FedpolApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fedpol.request import FedpolRequest
    from webob.response import Response


@FedpolApp.view(
    model=SiteLocale,
    permission=Public
)
def change_site_locale(
    self: SiteLocale,
    request: FedpolRequest
) -> Response:
    """ Changes the locale. """

    return self.redirect(request)
