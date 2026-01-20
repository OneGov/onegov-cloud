from __future__ import annotations

from onegov.core.i18n import SiteLocale
from onegov.core.security import Public
from onegov.org import OrgApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from webob import Response


@OrgApp.view(model=SiteLocale, permission=Public)
def change_site_locale(self: SiteLocale, request: OrgRequest) -> Response:
    return self.redirect(request)
