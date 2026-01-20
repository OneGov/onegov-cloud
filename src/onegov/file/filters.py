from __future__ import annotations

import os
import shlex
import logging
import subprocess

from depot.fields.interfaces import FileFilter
from depot.io.utils import file_from_content
from io import BytesIO

from onegov.core.utils import module_path
from onegov.file.utils import IMAGE_MIME_TYPES, get_image_size
from pathlib import Path
from PIL import Image, ImageOps
from tempfile import TemporaryDirectory


from typing import IO, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRead
    from depot.fields.upload import UploadedFile


log = logging.getLogger('onegov.file')


class ConditionalFilter(FileFilter):
    """ A depot filter that's only run if a condition is met. The condition
    is defined by overriding the :meth:``meets_condition`` returns True.

    """

    def __init__(self, filter: FileFilter):
        self.filter = filter

    def meets_condition(self, uploaded_file: UploadedFile) -> bool:
        raise NotImplementedError

    def on_save(self, uploaded_file: UploadedFile) -> None:
        if self.meets_condition(uploaded_file):
            self.filter.on_save(uploaded_file)


class OnlyIfImage(ConditionalFilter):
    """ A conditional filter that runs the passed filter only if the
    uploaded file is an image.

    """

    def meets_condition(self, uploaded_file: UploadedFile) -> bool:
        return uploaded_file.content_type in IMAGE_MIME_TYPES


class OnlyIfPDF(ConditionalFilter):
    """ A conditional filter that runs the passed filter only if the
    uploaded file is a pdf.

    """

    def meets_condition(self, uploaded_file: UploadedFile) -> bool:
        return uploaded_file.content_type == 'application/pdf'


class WithThumbnailFilter(FileFilter):
    """ Uploads a thumbnail together with the file.

    Takes for granted that the file is an image.

    The resulting uploaded file will provide an additional property
    ``thumbnail_name``, which will contain the id and the path to the
    thumbnail. The name is replaced with the name given to the filter.

    .. warning::

        Requires Pillow library

    Note: This has been copied from Depot and adjusted for our use. Changes
    include a different storage format, no storage of the url and replacement
    of thumbnails instead of recreation (if possible).

    """

    quality = 90

    def __init__(self, name: str, size: tuple[int, int], format: str):
        self.name = name
        self.size = size
        self.format = format.lower()

    def generate_thumbnail(
        self,
        fp: IO[bytes]
    ) -> tuple[BytesIO, tuple[str, str]]:
        output = BytesIO()

        thumbnail: Image.Image = Image.open(fp)
        ImageOps.exif_transpose(thumbnail, in_place=True)
        thumbnail.thumbnail(self.size, Image.Resampling.LANCZOS)
        thumbnail = thumbnail.convert('RGBA')

        thumbnail.save(output, self.format, quality=self.quality)
        output.seek(0)

        return output, get_image_size(thumbnail)

    def store_thumbnail(
        self,
        uploaded_file: UploadedFile,
        fp: IO[bytes],
        thumbnail_size: tuple[str, str] | None = None,
    ) -> None:

        name = f'thumbnail_{self.name}'
        filename = f'thumbnail_{self.name}.{self.format}'

        path, id = uploaded_file.store_content(fp, filename)

        if thumbnail_size is None:
            thumbnail_size = get_image_size(Image.open(fp))

        uploaded_file[name] = {
            'id': id,
            'path': path,
            'size': thumbnail_size
        }

    def on_save(self, uploaded_file: UploadedFile) -> None:
        close, fp = file_from_content(uploaded_file.original_content)
        thumbnail_fp, thumbnail_size = self.generate_thumbnail(fp)
        self.store_thumbnail(uploaded_file, thumbnail_fp, thumbnail_size)
        if close:
            fp.close()


class WithPDFThumbnailFilter(WithThumbnailFilter):
    """ Uploads a preview thumbnail as PNG together with the file.

    This is basically the PDF implementation for `WithThumbnailFilter`.

    .. warning::

        Requires the presence of ghostscript (gs binary) on the PATH.

    """

    downscale_factor = 4

    def generate_preview(self, fp: SupportsRead[bytes]) -> BytesIO:
        with TemporaryDirectory() as directory:
            path = Path(directory)

            pdf_input = path / 'input.pdf'
            png_output = path / 'preview.png'

            with pdf_input.open('wb') as pdf:
                pdf.write(fp.read())

            process = subprocess.run((  # nosec:B603
                'gs',

                # disable read/writes outside of the given files
                '-dSAFER',
                '-dPARANOIDSAFER',

                # do not block for any reason
                '-dBATCH',
                '-dNOPAUSE',
                '-dNOPROMPT',

                # limit output messages
                '-dQUIET',
                '-sstdout=/dev/null',

                # format the page for thumbnails
                '-dPDFFitPage',

                # render in high resolution before downscaling to 72 dpi
                f'-r{self.downscale_factor * 72}',
                f'-dDownScaleFactor={self.downscale_factor}',

                # only use the first page
                '-dLastPage=1',

                # output to png
                '-sDEVICE=png16m',
                '-sOutputFile={}'.format(shlex.quote(str(png_output))),

                # from pdf
                str(pdf_input)
            ))

            process.check_returncode()

            with png_output.open('rb') as png:
                return BytesIO(png.read())

    def generate_thumbnail(
        self,
        fp: SupportsRead[bytes]
    ) -> tuple[BytesIO, tuple[str, str]]:
        # FIXME: This is kinda slow. We should be able to render the
        #        PDF directly at the thumbnail size. Maybe we should
        #        use pdf2image rather than roll our own?
        try:
            return super().generate_thumbnail(self.generate_preview(fp))
        except Exception as e:
            log.warning(f'Thumbnail generation failed: {e!s}')
            fallback = BytesIO()
            icon_path = (
                    module_path('onegov.org', 'static/pdf_preview')
                    + os.sep
                    + 'thumbnail_medium_pdf_preview_fallback.png'
            )
            with open(icon_path, 'rb') as f:
                fallback.write(f.read())
            fallback.seek(0)
            return super().generate_thumbnail(fallback)
