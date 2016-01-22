import onegov.onboarding

from onegov.testing import utils
from webtest import TestApp as Client


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.onboarding)


def test_default_assistant(onboarding_app):
    c = Client(onboarding_app)
    assert c.get('/').follow().request.url.endswith('for-towns/1')
