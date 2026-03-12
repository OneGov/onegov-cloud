from __future__ import annotations

from onegov.user.sync import UserSource
from onegov.user.utils import password_reset_url
from onegov.user.collections import UserCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class DummyRequest():
    client_addr = '127.0.0.1'

    def new_url_safe_token(self, token: dict[str, str]) -> str:
        return '-'.join('_'.join(pair) for pair in sorted(token.items()))


def test_password_reset_url(session: Session) -> None:
    request: Any = DummyRequest()
    user = UserCollection(session).register('usr', 'very_secret', request)

    url = password_reset_url(user, request, 'http://localhost/reset')
    assert url == 'http://localhost/reset?token=modified_-username_usr'

    url = password_reset_url(user, request, 'http://localhost/reset?extra')
    assert url == 'http://localhost/reset?extra&token=modified_-username_usr'

    url = password_reset_url(user, request, 'http://localhost/reset?p=1&p=2')
    assert url == 'http://localhost/reset?p=1&p=2&token=modified_-username_usr'


def test_user_source() -> None:

    data: Any = {
        'default_filter': '(mail=*@aba-zug.ch)',
        'org': 'VD / ABA',
        'bases': ['ou=aba,ou=SchulNet,o=Extern']
    }
    source = UserSource('Test', **data)
    assert source.filters == [data['default_filter']]

    data['filters'] = ['testing-a', 'testing-b']
    data['bases'] = ['a', 'b']
    source = UserSource('CustomFilters', **data)
    assert source.filters == ['testing-a', 'testing-b']
