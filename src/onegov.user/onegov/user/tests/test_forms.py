from onegov.user import UserCollection
from onegov.user.forms import LoginForm
from mock import Mock


def test_login_form(session):
    UserCollection(session).add('root@example.org', '123456', 'root')

    request = Mock()
    request.app = Mock()
    request.app.session = Mock(return_value=session)
    request.app.application_id = 'my-app'

    form = LoginForm(data={'email': '', 'password': ''})
    assert form.get_identity(request) is None

    form = LoginForm(data={'email': 'root@example.org', 'password': ''})
    assert form.get_identity(request) is None

    form = LoginForm(data={'email': '', 'password': '123456'})
    assert form.get_identity(request) is None

    form = LoginForm(data={'email': 'root@exampleorg', 'password': '123456'})
    assert form.get_identity(request) is None

    form = LoginForm(data={'email': 'root@example.org', 'password': '123456'})
    identity = form.get_identity(request)

    assert identity is not None
    assert identity.userid == 'root@example.org'
    assert identity.role == 'root'
    assert identity.application_id == 'my-app'
