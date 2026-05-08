from __future__ import annotations

from webtest import TestApp as Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestApp


def test_view_home(swissvotes_app: TestApp) -> None:
    client = Client(swissvotes_app)
    home = client.get('/').maybe_follow()
    assert "<h2>home</h2>" in home
    assert home.request.url.endswith('page/home')
