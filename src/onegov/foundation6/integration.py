from __future__ import annotations

from onegov.core import Framework
from onegov.core.layout import ChameleonLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest


class FoundationApp(Framework):
    pass


@FoundationApp.webasset_path()
def get_foundation_js_path() -> str:
    return 'assets'


@FoundationApp.webasset('foundation6')
def get_foundation_js_assets() -> Iterator[str]:
    yield 'jquery.js'
    yield 'what-input.js'
    yield 'foundation.min.js'
    yield 'foundation-init.js'


class FoundationLayout(ChameleonLayout):
    def __init__(self, model: object, request: CoreRequest):
        super().__init__(model, request)
        self.request.include('foundation6')
