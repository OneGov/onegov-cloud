import hashlib

from depot.fields.upload import UploadedFile
from depot.io import utils
from depot.io.interfaces import FileStorage
from depot.io.utils import INMEMORY_FILESIZE
from onegov.file.utils import IMAGE_MIME_TYPES
from PIL import Image
from tempfile import SpooledTemporaryFile


IMAGE_MAX_SIZE = 1024
IMAGE_QUALITY = 90
CHECKSUM_FUNCTION = hashlib.md5


def limit_image_size(file, content, content_type):

    if content_type not in IMAGE_MIME_TYPES:
        return None

    image = Image.open(content)

    if max(image.size) > IMAGE_MAX_SIZE:
        image.thumbnail((IMAGE_MAX_SIZE, IMAGE_MAX_SIZE), Image.LANCZOS)
        content = SpooledTemporaryFile(INMEMORY_FILESIZE)
        image.save(content, image.format, quality=IMAGE_QUALITY)

    return content


def calculate_checksum(content):
    checksum = CHECKSUM_FUNCTION()

    for chunk in iter(lambda: content.read(4096), b""):
        checksum.update(chunk)

    return checksum.hexdigest()


def store_checksum(file, content, content_type):
    file.checksum = calculate_checksum(content)


class ProcessedUploadedFile(UploadedFile):

    processors = (store_checksum, limit_image_size)

    def process_content(self, content, filename=None, content_type=None):
        filename, content_type = FileStorage.fileinfo(content)[1:]
        content = utils.file_from_content(content)

        for processor in self.processors:
            content = processor(self, content, content_type) or content
            content.seek(0)

        super().process_content(content, filename, content_type)
