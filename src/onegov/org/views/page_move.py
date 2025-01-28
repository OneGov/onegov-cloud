from __future__ import annotations

from onegov.core.security import Private
from onegov.org import OrgApp
from onegov.org.models import PageMove


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


@OrgApp.view(model=PageMove, permission=Private, request_method='PUT')
def move_page(self: PageMove, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    self.execute()
