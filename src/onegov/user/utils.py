from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.user import User
    from onegov.core.request import CoreRequest


def password_reset_url(
    user: User,
    request: CoreRequest,
    url: str
) -> str | None:
    """ Appends the token needed by PasswordResetForm for a password reset.

    :user:
        The user (model).

    :request:
        The request.

    :url:
        The URL which points to the password reset view (which is using the
        PasswordResetForm).

    :return: An URL containg the password reset token, or None if unsuccesful.

    """

    # external users may not reset their passwords here
    if user.source is not None:
        return None

    token = request.new_url_safe_token({
        'username': user.username,
        'modified': user.modified.isoformat() if user.modified else ''
    })

    # we can skip a lot of complexity, because we know the token is
    # already url safe, so we don't need to do a quote_plus
    delimeter = '&' if '?' in url else '?'
    return f'{url}{delimeter}token={token}'
