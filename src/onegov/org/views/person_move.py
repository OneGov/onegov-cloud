from onegov.core.security import Private
from onegov.org import OrgApp
from onegov.org.models import PersonMove


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


@OrgApp.view(model=PersonMove, permission=Private, request_method='PUT')
def move_page(self: PersonMove[Any], request: 'OrgRequest') -> None:
    request.assert_valid_csrf_token()
    self.execute()
