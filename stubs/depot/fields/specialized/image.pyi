from depot.fields.upload import UploadedFile
from depot.io.interfaces import StoredFile

class UploadedImageWithThumb(UploadedFile):
    max_size: int
    thumbnail_format: str
    thumbnail_size: tuple[int, int]
    @property
    def thumb_file(self) -> StoredFile: ...
    @property
    def thumb_url(self) -> str: ...
