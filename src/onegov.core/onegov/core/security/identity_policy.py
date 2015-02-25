from more.itsdangerous import IdentityPolicy as BaseIdentityPolicy


class IdentityPolicy(BaseIdentityPolicy):

    @property
    def cookie_settings(self):
        return {
            'max_age': self.max_age,
            'secure': self.current_request.app.identity_secure,
            'httponly': True
        }

    @property
    def secret(self):
        return self.current_rquest.app.identity_secret_key

    def identify(self, request):
        self.current_request = request
        return super(IdentityPolicy, self).identify(request)

    def remember(self, response, request, identity):
        self.current_request = request
        return super(IdentityPolicy, self).remember(
            response, request, identity)

    def forget(self, response, request):
        self.current_request = request
        return super(IdentityPolicy, self).identify(response, request)
