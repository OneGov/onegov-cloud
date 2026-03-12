from __future__ import annotations

from onegov.core import filters  # noqa -> registers webasset filters


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import App


def test_integration(app: App) -> None:
    assert app.rate_limit == (100, 900)
