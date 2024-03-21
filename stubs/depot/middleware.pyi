from _typeshed.wsgi import StartResponse, WSGIApplication, WSGIEnvironment
from collections.abc import Iterable
from datetime import datetime

from depot.io.interfaces import StoredFile

class FileServeApp:
    file: StoredFile
    filename: str
    last_modified: datetime
    content_length: int
    content_type: str
    cache_expires: int
    replace_wsgi_filewrapper: bool
    def __init__(self, storedfile: StoredFile, cache_max_age: int, replace_wsgi_filewrapper: bool = False) -> None: ...
    def generate_etag(self) -> str: ...
    def parse_date(self, value: str) -> datetime: ...
    @classmethod
    def make_date(cls, d: datetime | float) -> str: ...
    def has_been_modified(self, environ: WSGIEnvironment, etag: str, last_modified: datetime) -> bool: ...
    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]: ...

class DepotMiddleware:
    app: WSGIApplication
    mountpoint: str
    cache_max_age: int
    replace_wsgi_filewrapper: bool
    def __init__(self, app: WSGIApplication, mountpoint: str = "/depot", cache_max_age: int = 604800, replace_wsgi_filewrapper: bool = False) -> None: ...
    def url_for(self, path: str) -> str: ...
    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]: ...
