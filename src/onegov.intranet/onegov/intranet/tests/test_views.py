import onegov.intranet
import onegov.intranet.IntranetApp

from onegov_testing import utils


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.org, onegov.org.IntranetApp)
