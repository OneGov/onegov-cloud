from morepath import Identity
from onegov.core.framework import Framework


class IdentityPolicy(object):
    """ Stores the tokens associated with the identity on the browser session

    """

    required_keys = {'userid', 'role', 'application_id'}

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
        for key in self.required_keys:
            if request.browser_session.has(key):
                del request.browser_session[key]


@Framework.identity_policy()
def identity_policy():
    return IdentityPolicy()


@Framework.verify_identity()
def verify_identity(identity):
    # trust the identity established by the identity policy (we could keep
    # checking if the user is really in the database here - or if it was
    # removed in the meantime)
    return True
