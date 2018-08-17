from onegov.user.utils import password_reset_url
from onegov.user.collections import UserCollection


class DummyRequest():
    client_addr = '127.0.0.1'

    def new_url_safe_token(self, token):
        return '-'.join(['_'.join(pair) for pair in sorted(token.items())])


def test_password_reset_url(session):
    request = DummyRequest()
    user = UserCollection(session).register('usr', 'very_secret', request)

    url = password_reset_url(user, request, 'http://localhost/reset')
    assert url == 'http://localhost/reset?token=modified_-username_usr'

    url = password_reset_url(user, request, 'http://localhost/reset?extra')
    assert url == 'http://localhost/reset?extra&token=modified_-username_usr'

    url = password_reset_url(user, request, 'http://localhost/reset?p=1&p=2')
    assert url == 'http://localhost/reset?p=1&p=2&token=modified_-username_usr'
