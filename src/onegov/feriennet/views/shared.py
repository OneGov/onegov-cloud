from __future__ import annotations

from onegov.user import User, UserCollection
from sqlalchemy import func


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest


def users_for_select_element(request: FeriennetRequest) -> tuple[User, ...]:
    u = UserCollection(request.session).query()
    u = u.with_entities(User.id, User.username, User.title, User.realname)
    u = u.order_by(func.lower(User.title))
    u = u.filter_by(active=True)
    return tuple(u)
