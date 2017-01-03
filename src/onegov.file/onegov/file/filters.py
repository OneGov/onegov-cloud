from depot.fields.interfaces import FileFilter
from depot.io.utils import file_from_content
from onegov.file.utils import IMAGE_MIME_TYPES, get_image_size
from PIL import Image
from io import BytesIO


class ConditionalFilter(FileFilter):
    """ A depot filter that's only run if a condition is met. The condition
    is defined by overriding the :meth:``meets_condition`` returns True.

    """

    def __init__(self, filter):
        self.filter = filter

    def meets_condition(self, uploaded_file):
        raise NotImplementedError

    def on_save(self, uploaded_file):
        if self.meets_condition(uploaded_file):
            self.filter.on_save(uploaded_file)


class OnlyIfImage(ConditionalFilter):
    """ A conditional filter that runs the passed filter only if the
    uploaded file is an image.

    """

    def meets_condition(self, uploaded_file):
        return uploaded_file.content_type in IMAGE_MIME_TYPES


class WithThumbnailFilter(FileFilter):
    """Uploads a thumbnail together with the file.

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

    def __init__(self, name, size, format):
        self.name = name
        self.size = size
        self.format = format.lower()

    def on_save(self, uploaded_file):
        content = file_from_content(uploaded_file.original_content)

        thumbnail = Image.open(content)
        thumbnail.thumbnail(self.size, Image.LANCZOS)
        thumbnail = thumbnail.convert('RGBA')
        thumbnail.format = self.format

        output = BytesIO()
        thumbnail.save(output, self.format, quality=self.quality)
        output.seek(0)

        name = 'thumbnail_{}'.format(self.name)
        filename = 'thumbnail_{}.{}'.format(self.name, self.format)

        path, id = uploaded_file.store_content(output, filename)

        uploaded_file[name] = {
            'id': id,
            'path': path,
            'size': get_image_size(thumbnail)
        }
