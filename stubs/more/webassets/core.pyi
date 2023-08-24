from collections.abc import Callable
from typing import Any

from dectate import directive
from morepath.app import App
from morepath.request import Request
from morepath.response import Response
from . import directives

class IncludeRequest(Request):
    included_assets: set[str]
    def include(self, resource: str) -> None: ...

class WebassetsApp(App):
    webasset_path = directive(directives.WebassetPath)
    webasset_output = directive(directives.WebassetOutput)
    webasset_filter = directive(directives.WebassetFilter)
    webasset_mapping = directive(directives.WebassetMapping)
    webasset_url = directive(directives.WebassetUrl)
    webasset = directive(directives.Webasset)

def webassets_injector_tween(app: WebassetsApp, handler: Callable[[Request], Response]) -> Callable[[Request], Response]: ...
