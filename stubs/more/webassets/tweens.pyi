from _typeshed import StrOrBytesPath
from collections.abc import Callable, Iterator
from urllib.parse import unquote as unquote

from more.webassets.core import IncludeRequest
from morepath.request import Request, Response
from webassets import Environment

CONTENT_TYPES: set[str]
METHODS: set[str]
FOREVER: float

def is_subpath(directory: StrOrBytesPath, path: StrOrBytesPath) -> bool: ...
def has_insecure_path_element(path: str) -> bool: ...

class InjectorTween:
    environment: Environment
    handler: Callable[[Request], Response]
    def __init__(self, environment: Environment, handler: Callable[[Request], Response]) -> None: ...
    def urls_by_resource(self, resource: str) -> list[str]: ...
    def urls_to_inject(self, request: IncludeRequest, suffix: str | None = None) -> Iterator[str]: ...
    def __call__(self, request: IncludeRequest) -> Response: ...

class PublisherTween:
    environment: Environment
    handler: Callable[[Request], Response]
    def __init__(self, environment: Environment, handler: Callable[[Request], Response]) -> None: ...
    def __call__(self, request: Request) -> Response: ...
