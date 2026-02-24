from __future__ import annotations

from webtest import TestApp as Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestApp



def test_view_exceptions(swissvotes_app: TestApp) -> None:
    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    assert (
        "Sie versuchen eine Seite zu öffnen, für die Sie nicht autorisiert "
        "sind"
    ) in client.get('/votes/update', status=403)

    assert (
        "Die angeforderte Seite konnte nicht gefunden werden."
    ) in client.get('/abstimmungen', status=404)
