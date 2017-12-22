from onegov.core.custom import json
from onegov.user.utils import password_reset_url
from onegov.user.collections import UserCollection


class DummyRequest():
    client_addr = '127.0.0.1'

    def new_url_safe_token(self, token):
        return json.dumps(token, sort_keys=True)


def test_password_reset_url(session):
    request = DummyRequest()
    user = UserCollection(session).register(
        'info@example.com', 'very_secret', request
    )

    url = password_reset_url(user, request, 'http://localhost/reset')
    assert url == (
        'http://localhost/reset?'
        'token={"modified":"","username":"info@example.com"}'
    )
