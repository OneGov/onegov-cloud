from __future__ import annotations

from onegov.org.request import OrgRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.winterthur.app import WinterthurApp


# NOTE: This is currently only used for type checking
class WinterthurRequest(OrgRequest):
    app: WinterthurApp
