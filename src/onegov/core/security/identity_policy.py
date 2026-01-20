from __future__ import annotations

from morepath import Identity
from onegov.core.browser_session import BrowserSession
from onegov.core.framework import Framework


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath import Response
    from ..request import CoreRequest


class IdentityPolicy:
    """ Stores the tokens associated with the identity on the browser session

    """

    required_keys = {'userid', 'groupids', 'role', 'application_id'}

    def identify(self, request: CoreRequest) -> Identity | None:
        try:
            identifiers = {
                key: request.browser_session[key] for key in self.required_keys
            }
        except KeyError:
            # FIXME: According to docs this should return NO_IDENTITY
            return None
        else:
            return Identity(**identifiers)

    def remember(
        self,
        response: Response,
        request: CoreRequest,
        identity: Identity
    ) -> None:
        for key in self.required_keys:
            request.browser_session[key] = getattr(identity, key)

    def forget(self, response: Response, request: CoreRequest) -> None:
        request.browser_session.flush()
        # NOTE: While clearing "storage" should probably mostly be fine
        #       we do use it to store some long-lived preferences like
        #       search filters in Swissvotes. So it would be inconvenient
        #       if those disappeared on logout. If we ever start putting
        #       more sensitive data in localStorage, we may have to revisit
        #       that decision, or perform a more targeted clear of that
        #       specific sensitive data.
        response.headers['Clear-Site-Data'] = '"cache"'


@Framework.identity_policy()
def identity_policy() -> IdentityPolicy:
    return IdentityPolicy()


@Framework.verify_identity()
def verify_identity(identity: Identity) -> bool:
    # trust the identity established by the identity policy (we could keep
    # checking if the user is really in the database here - or if it was
    # removed in the meantime)
    return True


def forget(app: Framework, session_id: str) -> None:
    """ Clears the tokens associated with the identity from given browser
    session.

    """

    session = BrowserSession(app.session_cache, session_id)
    session.flush()


def remembered(app: Framework, session_id: str) -> bool:
    """ Checks if tokens associated with the identity are stored for the given
    browser session.

    """
    session = BrowserSession(app.session_cache, session_id)
    for key in IdentityPolicy.required_keys:
        if session.has(key):
            return True

    return False
