from collections.abc import Sequence
from sqlalchemy import types
from typing import Any, Literal

from depot.fields.interfaces import FileFilter
from depot.fields.upload import UploadedFile

class UploadedFileField(types.TypeDecorator):
    impl = types.Unicode
    cache_ok: Literal[True]
    def __init__(self, filters: Sequence[FileFilter] = (), upload_type: type[UploadedFile] = ..., upload_storage: str | None = ..., *args: Any, **kw: Any) -> None: ...
