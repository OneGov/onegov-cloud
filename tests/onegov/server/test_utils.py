from __future__ import annotations

from onegov.server.utils import load_class
from onegov.server.core import Server


def test_load_class() -> None:
    assert load_class('onegov.server.Server') is Server
    assert load_class('onegov.server.core.Server') is Server
    assert load_class(Server) is Server
    assert load_class('onegov.server.Foobar') is None
