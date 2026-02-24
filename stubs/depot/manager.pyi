from _typeshed import StrPath
from _typeshed.wsgi import WSGIApplication
from typing import Any

from depot.io.interfaces import FileStorage, StoredFile
from depot.middleware import DepotMiddleware

class DepotManager:
    _default_depot: str | None
    _depots: dict[str, FileStorage]
    _aliases: dict[str, str]

    @classmethod
    def set_default(cls, name: str) -> None: ...
    @classmethod
    def get_default(cls) -> str: ...
    @classmethod
    def set_middleware(cls, mw: DepotMiddleware) -> None: ...
    @classmethod
    def get_middleware(cls) -> DepotMiddleware: ...
    @classmethod
    def get(cls, name: str | None = None) -> FileStorage | None: ...
    @classmethod
    def get_file(cls, path: str) -> StoredFile: ...
    @classmethod
    def url_for(cls, path: StrPath) -> str: ...
    @classmethod
    def configure(cls, name: str, config: dict[str, Any], prefix: str = "depot.") -> FileStorage: ...
    @classmethod
    def alias(cls, alias: str, name: str) -> None: ...
    @classmethod
    def resolve_alias(cls, name: str) -> str: ...
    @classmethod
    def make_middleware(cls, app: WSGIApplication, **options: Any) -> DepotMiddleware: ...
    @classmethod
    def from_config(cls, config: dict[str, Any], prefix: str = "depot.") -> FileStorage: ...

get_depot = DepotManager.get
get_file = DepotManager.get_file
configure = DepotManager.configure
set_default = DepotManager.set_default
