import onegov.intranet

from onegov.intranet import IntranetApp
from onegov_testing import utils


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.org, IntranetApp)
