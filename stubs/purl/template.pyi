from collections.abc import Mapping

from .url import URL

__all__ = ["Template", "expand"]

class Template:
    def __init__(self, url_str: str) -> None: ...
    def expand(self, variables: Mapping[str, object] | None = None) -> URL: ...

def expand(template: str, variables: Mapping[str, object] | None = None) -> str: ...
