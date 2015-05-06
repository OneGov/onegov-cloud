""" Contains the models describing the images. """

import PIL

from onegov.core.filestorage import FilestorageFile
from webob.exc import HTTPUnsupportedMediaType


class ImageCollection(object):
    """ Defines the collection of images uploaded to the site. Currently
    this is done without any ORM backing (and therefore without any
    special features like tagging, metadata and so on).

    Instead it's simply a list of images in a directory.

    This can be made more powerful (and complicated) once we have sufficent
    time to do it.

    """

    thumbnail_dimension = (256, 256)
    thumbnail_quality = 80
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    thumbnail_extensions = {'png', 'jpg', 'jpeg', 'gif'}

    def __init__(self, app):
        assert app.has_filestorage

        self.path_prefix = 'images/'
        self.image_storage = app.filestorage.makeopendir('images')
        self.thumbnail_storage = self.image_storage.makeopendir('thumbnails')

    @property
    def images(self):
        """ Returns the :class:`~onegov.town.model.Image` instances in this
        collection.

        """
        images = self.image_storage.ilistdirinfo(files_only=True)
        images = sorted(images, key=lambda i: i[1]['created_time'])

        for filename, info in images:
            yield Image(filename, info)

    @property
    def thumbnails(self):
        """ Returns the :class:`~onegov.town.model.Thumbnail` instances in this
        collection.

        """
        images = self.thumbnail_storage.ilistdirinfo(files_only=True)
        images = sorted(images, key=lambda i: i[1]['created_time'])

        for filename, info in images:
            yield Thumbnail(filename, info)

    def store_image(self, image, filename):
        """ Stores an image (a file with a ``read()`` method) with the given
        filename. Note that these images are public, so the filename *should*
        be random.

        See :func:`onegov.core.filestorage.random_filename`.

        """
        extension = filename.split('.')[-1]

        if extension not in self.allowed_extensions:
            raise HTTPUnsupportedMediaType()

        self.image_storage.setcontents(filename, image.read())

        return self.get_image_by_filename(filename)

    def get_image_by_filename(self, filename):
        """ Returns the :class:`~onegov.town.model.Image` instance with the
        given name, or None if not found.

        """
        if self.image_storage.exists(filename):
            return Image(filename)

    def get_thumbnail_by_filename(self, filename):
        """ Returns the :class:`~onegov.town.model.Thumbnail` instance with the
        given name, or None if not found.

        This method *generates* the thumbnail if it doesn't exist yet!

        """
        if not self.image_storage.exists(filename):
            return None

        if self.thumbnail_storage.exists(filename):
            return Thumbnail(filename)

        extension = filename.split('.')[-1]

        if extension not in self.thumbnail_extensions:
            return Image(filename)

        im = PIL.Image.open(self.image_storage.getsyspath(filename))
        im.thumbnail(self.thumbnail_dimension)
        im.save(
            self.thumbnail_storage.open(filename, 'wb'),
            PIL.Image.EXTENSION['.' + extension],
            quality=self.thumbnail_quality
        )

        return Thumbnail(filename)

    def delete_image_by_filename(self, filename):
        """ Deletes both the image and the thumbnail of the given filename. """

        if self.image_storage.exists(filename):
            self.image_storage.remove(filename)

        if self.thumbnail_storage.exists(filename):
            self.thumbnail_storage.remove(filename)


class ImageFile(FilestorageFile):
    """ A filestorage file that points to an image. """

    def __init__(self, filename, info=None):
        self.filename = filename
        self.info = info or {}

    @property
    def date(self):
        if 'date' in self.info:
            return self.info['created_time'].date()


class Image(ImageFile):
    """ A filestorage file that points to a full image (not a thumbnail). """

    @property
    def thumbnail(self):
        return Thumbnail(self.filename)

    @property
    def path(self):
        return 'images/' + self.filename


class Thumbnail(ImageFile):
    """ A filestorage file that points to a thumbnail or the original file
    storage file, if there can't be a thumbnail (say for ``*.svg``).

    Thumbnails are created on the fly and cached.

    """

    @property
    def image(self):
        return Image(self.filename)

    @property
    def path(self):
        return 'images/thumbnails/' + self.filename
