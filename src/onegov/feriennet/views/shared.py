from __future__ import annotations

from onegov.user import User, UserCollection
from sqlalchemy import func


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest
    from typing import NamedTuple
    from uuid import UUID

    class UserRow(NamedTuple):
        id: UUID
        username: str
        title: str
        realname: str | None


def users_for_select_element(request: FeriennetRequest) -> tuple[UserRow, ...]:
    return tuple(
        UserCollection(request.session).query()  # type: ignore[arg-type]
        .with_entities(User.id, User.username, User.title, User.realname)
        .order_by(func.lower(User.title))
        .filter_by(active=True)
    )
