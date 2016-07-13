from depot.fields.upload import UploadedFile
from depot.io import utils
from depot.io.interfaces import FileStorage
from depot.io.utils import INMEMORY_FILESIZE
from onegov.file.utils import IMAGE_MIME_TYPES
from PIL import Image
from tempfile import SpooledTemporaryFile


class UploadedFileWithMaxImageSize(UploadedFile):
    max_size = 1024
    quality = 90

    def limit_image_size(self, content):
        # Get a file object even if content was bytes
        content = utils.file_from_content(content)

        uploaded_image = Image.open(content)
        if max(uploaded_image.size) > self.max_size:
            uploaded_image.thumbnail(
                (self.max_size, self.max_size), Image.LANCZOS)
            content = SpooledTemporaryFile(INMEMORY_FILESIZE)
            uploaded_image.save(
                content, uploaded_image.format, quality=self.quality
            )

        content.seek(0)

        return content

    def process_content(self, content, filename=None, content_type=None):
        # As we are replacing the main file, we need to explicitly pass
        # the filename and content_type, so get them from the old content.
        filename, content_type = FileStorage.fileinfo(content)[1:]

        if content_type in IMAGE_MIME_TYPES:
            content = self.limit_image_size(content)

        super().process_content(content, filename, content_type)
