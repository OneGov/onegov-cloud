from __future__ import annotations

from onegov.user import UserCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.gazette.request import GazetteRequest
    from onegov.user import User
    from uuid import UUID


def get_user(request: GazetteRequest) -> User | None:
    username = request.identity.userid
    if username is None:
        return None

    session = request.session
    return UserCollection(session).by_username(username)


def get_user_and_group(
    request: GazetteRequest
) -> tuple[list[UUID], list[UUID]]:

    user = get_user(request)
    return (
        [user.id] if (user and not user.group) else [],
        [user.group.id] if (user and user.group) else []
    )
