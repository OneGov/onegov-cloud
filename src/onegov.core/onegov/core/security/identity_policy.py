from morepath import Identity
from onegov.core.browser_session import BrowserSession
from onegov.core.framework import Framework


class IdentityPolicy(object):
    """ Stores the tokens associated with the identity on the browser session

    """

    required_keys = {'userid', 'groupid', 'role', 'application_id'}

    def identify(self, request):
        try:
            identifiers = {
                key: request.browser_session[key] for key in self.required_keys
            }
        except KeyError:
            return None
        else:
            return Identity(**identifiers)

    def remember(self, response, request, identity):
        for key in self.required_keys:
            request.browser_session[key] = getattr(identity, key)

    def forget(self, response, request):
        request.browser_session.flush()


@Framework.identity_policy()
def identity_policy():
    return IdentityPolicy()


@Framework.verify_identity()
def verify_identity(identity):
    # trust the identity established by the identity policy (we could keep
    # checking if the user is really in the database here - or if it was
    # removed in the meantime)
    return True


def forget(app, session_id):
    """ Clears the tokens associated with the identity from given browser
    session.

    """

    session = BrowserSession(app.session_cache, session_id)
    session.flush()


def remembered(app, session_id):
    """ Checks if tokens associated with the identity are stored for the given
    browser session.

    """
    session = BrowserSession(app.session_cache, session_id)
    for key in IdentityPolicy.required_keys:
        if session.has(key):
            return True

    return False
