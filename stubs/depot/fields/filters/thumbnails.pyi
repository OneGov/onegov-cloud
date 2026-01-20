from depot.fields.interfaces import FileFilter
from depot.fields.upload import UploadedFile

class WithThumbnailFilter(FileFilter):
    thumbnail_size: tuple[int, int]
    thumbnail_format: str
    def __init__(self, size: tuple[int, int] = (128, 128), format: str = 'PNG') -> None: ...
    def on_save(self, uploaded_file: UploadedFile) -> None: ...
