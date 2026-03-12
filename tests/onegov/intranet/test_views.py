from __future__ import annotations

import onegov.intranet

from onegov.intranet import IntranetApp
from tests.shared import utils


def test_view_permissions() -> None:
    utils.assert_explicit_permissions(onegov.org, IntranetApp)
