import onegov.election_day

from onegov.testing import utils


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.election_day)
