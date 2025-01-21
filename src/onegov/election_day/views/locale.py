from __future__ import annotations

from onegov.core.i18n import SiteLocale
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.view(
    model=SiteLocale,
    permission=Public
)
def change_site_locale(
    self: SiteLocale,
    request: ElectionDayRequest
) -> Response:
    """ Changes the locale. """

    return self.redirect(request)
