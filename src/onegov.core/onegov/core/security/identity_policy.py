from cached_property import cached_property
from more.itsdangerous import IdentityPolicy as BaseIdentityPolicy
from onegov.core import Framework


class IdentityPolicy(BaseIdentityPolicy):

    @cached_property
    def required_keys(self):
        return ('userid', 'role', 'application_id')

    @property
    def cookie_settings(self):
        return {
            'max_age': self.max_age,
            'secure': self.current_request.app.identity_secure,
            'httponly': True
        }

    @property
    def secret(self):
        return self.current_request.app.identity_secret

    def identify(self, request):
        self.current_request = request
        return super(IdentityPolicy, self).identify(request)

    def remember(self, response, request, identity):
        self.current_request = request
        return super(IdentityPolicy, self).remember(
            response, request, identity)

    def forget(self, response, request):
        self.current_request = request
        return super(IdentityPolicy, self).forget(response, request)


@Framework.identity_policy()
def identity_policy():
    return IdentityPolicy()


@Framework.verify_identity()
def verify_identity(identity):
    # trust the identity established by the identity policy (we could keep
    # checking if the user is really in the database here - or if it was
    # removed in the meantime)
    return True
