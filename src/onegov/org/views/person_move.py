import json

from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.models import PersonMove
from webob.exc import HTTPConflict


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


@OrgApp.view(model=PersonMove, permission=Private, request_method='PUT')
def move_page(self: PersonMove[Any], request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    try:
        self.execute()
    except KeyError:
        message = request.translate(
            _(
                'The linked people have changed. Please reload the page '
                'before sorting again.'
            )
        )
        raise HTTPConflict(
            body=json.dumps({'message': message}).encode('utf-8'),
            content_type='application/json',
        ) from None
