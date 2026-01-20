from _typeshed import ReadableBuffer
from abc import ABCMeta, abstractmethod
from cgi import FieldStorage
from collections.abc import Callable, Iterable
from datetime import datetime
from io import IOBase
from typing import IO
from typing_extensions import TypeAlias

from depot.io.utils import FileIntent as FileIntent

_UUIDStr: TypeAlias = str
_FileContent: TypeAlias = bytes | IO[bytes] | FileIntent | FieldStorage

class _HasFilenameAndContentType:
    @property
    def filename(self) -> str: ...
    @property
    def content_type(self) -> str: ...

_HasFilenameAndContentTypeOrFactory: TypeAlias = _HasFilenameAndContentType | Callable[[], _HasFilenameAndContentType]

class StoredFile(IOBase, IO[bytes], metaclass=ABCMeta):
    file_id: _UUIDStr
    filename: str
    content_type: str
    last_modified: datetime
    content_length: int
    def __init__(
        self,
        file_id: _UUIDStr,
        filename: str | None = None,
        content_type: str | None = None,
        last_modified: str | None = None,
        content_length: str | None = None,
    ) -> None: ...
    def readable(self) -> bool: ...
    def writable(self) -> bool: ...
    def seekable(self) -> bool: ...
    @property
    def name(self) -> str: ...
    @abstractmethod
    def read(self, n: int = -1) -> bytes: ...
    @abstractmethod
    def close(self) -> None: ...
    @property
    @abstractmethod
    def closed(self) -> bool: ...
    @property
    def public_url(self) -> str | None: ...
    # the following two properties are just there to satisfy IO Protocol
    def __enter__(self) -> IO[bytes]: ...  # type:ignore[override]
    def writelines(self, lines: Iterable[ReadableBuffer], /) -> None: ...

class FileStorage(metaclass=ABCMeta):
    @staticmethod
    def fileid(file_or_id: StoredFile | _UUIDStr) -> _UUIDStr: ...
    @staticmethod
    def fileinfo(
        fileobj: _FileContent, filename: str | None = None, content_type: str | None = None, existing: _HasFilenameAndContentTypeOrFactory | None = None
    ) -> tuple[IO[bytes] | bytes, str, str]: ...
    @abstractmethod
    def get(self, file_or_id: StoredFile | str) -> StoredFile: ...
    @abstractmethod
    def create(self, content: _FileContent, filename: str | None = None, content_type: str | None = None) -> _UUIDStr: ...
    @abstractmethod
    def replace(self, file_or_id: StoredFile | _UUIDStr, content: _FileContent, filename: str | None = None, content_type: str | None = None) -> _UUIDStr: ...
    @abstractmethod
    def delete(self, file_or_id: StoredFile | _UUIDStr) -> None: ...
    @abstractmethod
    def exists(self, file_or_id: StoredFile | _UUIDStr) -> bool: ...
    @abstractmethod
    def list(self) -> list[str]: ...
