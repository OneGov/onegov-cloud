from __future__ import annotations

from morepath import Identity
from onegov.core.browser_session import BrowserSession
from onegov.core.framework import Framework


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath import Response
    from ..request import CoreRequest


# TODO: We could consider making frozenset MessagePack serializable, so we
#       don't need to special case groupids here
class IdentityPolicy:
    """ Stores the tokens associated with the identity on the browser session

    """

    required_keys = {'userid', 'role', 'application_id'}

    def identify(self, request: CoreRequest) -> Identity | None:
        try:
            identifiers = {
                key: request.browser_session[key] for key in self.required_keys
            }
            identifiers['groupids'] = frozenset(
                request.browser_session['groupids']
            )
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
        request.browser_session['groupids'] = tuple(identity.groupids)

    def forget(self, response: Response, request: CoreRequest) -> None:
        request.browser_session.flush()


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
