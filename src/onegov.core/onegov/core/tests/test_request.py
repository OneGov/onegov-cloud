from datetime import datetime, timedelta
from freezegun import freeze_time
from onegov.core.utils import Bunch
from onegov.core.request import CoreRequest


def test_url_safe_token():

    request = CoreRequest(environ={
        'PATH_INFO': '/',
        'SERVER_NAME': '',
        'SERVER_PORT': '',
        'SERVER_PROTOCOL': 'https'
    }, app=Bunch(identity_secret='asdf', lookup=None))

    token = request.new_url_safe_token({'foo': 'bar'})

    assert request.load_url_safe_token(token) == {'foo': 'bar'}
    assert request.load_url_safe_token(token, salt='x') is None

    with freeze_time(datetime.now() + timedelta(seconds=2)):
        assert request.load_url_safe_token(token, max_age=1) is None
