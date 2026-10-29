from __future__ import annotations

from onegov.core.i18n import SiteLocale
from onegov.core.security import Public
from onegov.ilz import ILZApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ilz.request import ILZRequest
    from webob.response import Response


@ILZApp.view(
    model=SiteLocale,
    permission=Public
)
def change_site_locale(
    self: SiteLocale,
    request: ILZRequest
) -> Response:
    """ Changes the locale. """

    return self.redirect(request)
