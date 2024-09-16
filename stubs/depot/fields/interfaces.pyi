from abc import ABCMeta, abstractmethod
from typing import Any

from depot.fields.upload import UploadedFile
from depot.io.interfaces import _FileContent

class FileFilter(metaclass=ABCMeta):
    @abstractmethod
    def on_save(self, uploaded_file: UploadedFile) -> None: ...

class DepotFileInfo(dict[str, Any], metaclass=ABCMeta):
    def __init__(self, content: object, depot_name: str | None = None) -> None: ...
    @abstractmethod
    def process_content(self, content: _FileContent, filename: str | None = None, content_type: str | None = None) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...
    def __delattr__(self, name: str) -> None: ...
