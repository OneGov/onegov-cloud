import pdftotext

from depot.fields.upload import UploadedFile
from depot.io import utils
from depot.io.interfaces import FileStorage
from depot.io.utils import INMEMORY_FILESIZE
from io import BytesIO
from onegov.core.html import sanitize_svg
from onegov.file.utils import digest
from onegov.file.utils import get_image_size
from onegov.file.utils import get_svg_size
from onegov.file.utils import IMAGE_MIME_TYPES
from onegov.file.utils import word_count
from PIL import Image, UnidentifiedImageError
from tempfile import SpooledTemporaryFile
from onegov.pdf.utils import extract_pdf_info


from typing import IO, TYPE_CHECKING
if TYPE_CHECKING:
    from typing_extensions import NotRequired, TypedDict

    class _ImageSaveOptionalParams(TypedDict):
        exif: NotRequired[Image.Exif]


IMAGE_MAX_SIZE = 2048
IMAGE_QUALITY = 85
CHECKSUM_FUNCTION = 'md5'


def get_svg_size_or_default(content: IO[bytes]) -> tuple[str, str]:
    width, height = get_svg_size(content)

    width = width if width is not None else f'{IMAGE_MAX_SIZE}px'
    height = height if height is not None else f'{IMAGE_MAX_SIZE}px'

    return width, height


def strip_exif_and_limit_and_store_image_size(
    file: 'ProcessedUploadedFile',
    content: IO[bytes],
    content_type: str | None
) -> IO[bytes] | None:

    if content_type == 'image/svg+xml':
        file.size = get_svg_size_or_default(content)

    if content_type not in IMAGE_MIME_TYPES:
        return None

    try:
        image = Image.open(content)
    except Image.DecompressionBombError:
        # reraise this one specifically
        raise
    except Exception:
        # treat any other internal error as an UnidentifierImageError
        raise UnidentifiedImageError from None

    needs_resample = max(image.size) > IMAGE_MAX_SIZE
    has_exif = bool(hasattr(image, 'getexif') and image.getexif())

    if needs_resample or has_exif:
        params: '_ImageSaveOptionalParams' = {}

        if has_exif:
            # replace EXIF section with an empty one
            params['exif'] = Image.Exif()

        if needs_resample:
            image.thumbnail(
                (IMAGE_MAX_SIZE, IMAGE_MAX_SIZE), Image.Resampling.LANCZOS
            )

        content = SpooledTemporaryFile(INMEMORY_FILESIZE)
        try:
            # Quality is only supported by jpeg
            image.save(content, image.format, quality=IMAGE_QUALITY, **params)
        except ValueError:
            image.save(content, image.format, **params)

    # the file size is stored in pixel as string (for browser usage)
    file.size = get_image_size(image)

    return content


def store_checksum(
    file: 'ProcessedUploadedFile',
    content: IO[bytes],
    content_type: str | None
) -> None:

    file.checksum = digest(content, type=CHECKSUM_FUNCTION)


def sanitize_svg_images(
    file: 'ProcessedUploadedFile',
    content: IO[bytes],
    content_type: str | None
) -> IO[bytes]:

    if content_type == 'image/svg+xml':
        sane_svg = sanitize_svg(content.read().decode('utf-8'))
        content = BytesIO(sane_svg.encode('utf-8'))

    return content


def store_extract_and_pages(
    file: 'ProcessedUploadedFile',
    content: IO[bytes],
    content_type: str | None
) -> None:

    if content_type == 'application/pdf':
        pages, file.extract = extract_pdf_info(content)

        file.stats = {
            'pages': pages,
            'words': word_count(file.extract)
        }


class ProcessedUploadedFile(UploadedFile):

    processors = (
        store_checksum,
        strip_exif_and_limit_and_store_image_size,
        sanitize_svg_images,
        store_extract_and_pages,
    )

    def process_content(
        self,
        content: IO[bytes],
        filename: str | None = None,
        content_type: str | None = None
    ) -> None:

        filename, content_type = FileStorage.fileinfo(content)[1:]
        content = utils.file_from_content(content)

        try:
            for processor in self.processors:
                content = processor(self, content, content_type) or content
                content.seek(0)
        except Image.DecompressionBombError:
            # not a real content type - but useful for us to be able to rely
            # on anything uploaded having a content type, even though that
            # content is discarded soon afterwards
            content = b''  # type:ignore[assignment]
            content_type = 'application/malicious'
        except UnidentifiedImageError:
            # also not a real content type
            content = b''  # type:ignore[assignment]
            content_type = 'application/unidentified-image'
        except pdftotext.Error:
            # signed pdfs have shown to be difficult to handle by pdftotext
            # it uses poppler apt package in the background resulting in old
            # versions installed on the host. We still would like to sign
            # the pdfs in which case file.stats has hopefully been set already
            pass

        super().process_content(content, filename, content_type)
