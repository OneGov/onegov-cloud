from __future__ import annotations

from onegov.core import Framework
from onegov.core.layout import ChameleonLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest


class BootstrapApp(Framework):
    pass


@BootstrapApp.webasset_path()
def get_bootstrap_js_path() -> str:
    return 'assets'


@BootstrapApp.webasset('bootstrap')
def get_bootstrap_js_assets() -> Iterator[str]:
    yield 'bootstrap.bundle.min.js'


class BootstrapLayout(ChameleonLayout):
    def __init__(self, model: object, request: CoreRequest):
        super().__init__(model, request)
        self.request.include('bootstrap')
