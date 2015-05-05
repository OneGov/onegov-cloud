""" Contains the models directly provided by onegov.town. """

import PIL

from onegov.core.filestorage import FilestorageFile
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.town.theme import user_colors
from sqlalchemy import Column, Text
from uuid import uuid4
from webob.exc import HTTPUnsupportedMediaType


class Town(Base, TimestampMixin):
    """ Defines the basic information associated with a town.

    It is assumed that there's only one town record in the schema associated
    with this town.
    """

    __tablename__ = 'towns'

    #: the id of the town, an automatically generated uuid
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the name of the town (as registered with the Swiss governement)
    name = Column(Text, nullable=False)

    #: the logo of the town
    logo_url = Column(Text, nullable=True)

    #: the theme options of the town
    theme_options = Column(JSON, nullable=True, default=user_colors.copy)


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
    storage file, if there can't be a thumbnail (say for *.svg).

    Thumbnails are created on the fly and cached.

    """

    @property
    def image(self):
        return Image(self.filename)

    @property
    def path(self):
        return 'images/thumbnails/' + self.filename


class Editor(object):
    """ Defines the model for the page editor. Required because pages need
    to be edited outside their url structure, since their urls are absorbed
    completely and turned into SQL queries.

    """
    def __init__(self, action, page):
        """ The editor is defined by an action and a page/context.

        :action:
            One of 'new', 'edit' or 'delete'.

        :page:
            The 'context' of the action. The actual page in the case of 'edit'
            and 'delete'. The parent in the case of 'new'.

        """

        self.action = action
        self.page = page

    @property
    def page_id(self):
        return self.page.id


class PageEditor(Editor):
    """ Editor for the page type "page". """
    pass


class LinkEditor(Editor):
    """ Editor for the page type "link". """
    pass
