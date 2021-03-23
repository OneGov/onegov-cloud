import onegov.core
import onegov.org
from tests.shared import utils


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.org, onegov.org.OrgApp)


def test_notfound(client):
    notfound_page = client.get('/foobar', expect_errors=True)
    assert "Seite nicht gefunden" in notfound_page
    assert notfound_page.status_code == 404
