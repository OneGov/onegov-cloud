from __future__ import annotations

from onegov.core.i18n import SiteLocale
from onegov.ilz import ILZApp


@ILZApp.path(
    model=SiteLocale,
    path='/locale/{locale}'
)
def get_locale(
    app: ILZApp,
    locale: str
) -> SiteLocale | None:
    return SiteLocale.for_path(app, locale)
