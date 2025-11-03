from __future__ import annotations

from onegov.pas.layouts import DefaultLayout
from onegov.core.utils import Bunch


from typing import Any


def test_layouts() -> None:
    request: Any = Bunch(
        app=Bunch(
            org=Bunch(
                geo_provider=None,
                open_files_target_blank=False
            ),
            schema='foo',
            sentry_dsn=None,
            version='1.0',
            websockets_client_url=lambda x: x,
            websockets_private_channel=None
        ),
        include=lambda x: x,
        is_manager=True
    )

    layout = DefaultLayout(None, request)
    assert layout.format_minutes(None) == ''
    assert layout.format_minutes(0) == ''
    assert layout.format_minutes(-20) == ''
    assert layout.format_minutes(10).interpolate() == '10 minutes'  # type: ignore[attr-defined]
    assert layout.format_minutes(60).interpolate() == '1 hours'  # type: ignore[attr-defined]
    assert layout.format_minutes(123).interpolate() == '2 hours 3 minutes'  # type: ignore[attr-defined]
