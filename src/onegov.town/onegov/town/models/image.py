""" Contains the models describing the images. """

import PIL

from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import date
from onegov.town import _
from onegov.town.models import File
from onegov.town.models import FileCollection


class ImageCollection(FileCollection):
    """ Defines the collection of images uploaded to the site. Currently
    this is done without any ORM backing (and therefore without any
    special features like tagging, metadata and so on).

    Instead it's simply a list of images in a directory.

    This can be made more powerful (and complicated) once we have sufficent
    time to do it.

    """

    thumbnail_dimension = (256, 256)
    thumbnail_quality = 80
    allowed_mime = {'image/png', 'image/jpeg', 'image/gif', 'image/svg+xml'}
    thumbnail_extensions = {'png', 'jpg', 'jpeg', 'gif'}

    def __init__(self, app):
        assert app.has_filestorage

        self.path_prefix = 'images/'
        self.file_storage = app.filestorage.makeopendir('images')
        self.thumbnail_storage = self.file_storage.makeopendir('thumbnails')

    @property
    def files(self):
        """ Returns the :class:`~onegov.town.model.Image` instances in this
        collection.

        """

        images = self.file_storage.ilistdirinfo(files_only=True)
        images = sorted(images, key=lambda i: i[1]['modified_time'])

        for filename, info in images:
            yield Image(filename, info)

    def grouped_files(self, today=None):
        """ Returns the :class:`~onegov.town.model.Image` instances in this
        collection grouped by natural language dates.
        """
        if today is None:
            today = date.today()
        this_month = datetime(today.year, today.month, 1)
        ranges = [
            [_('This month'), this_month],
            [_('Last month'), this_month - relativedelta(months=1)],
            [_('This year'), datetime(today.year, 1, 1)],
            [_('Last year'), datetime(today.year - 1, 1, 1)],
            [_('Older'), datetime(today.year - 2, 1, 1)],
        ]
        ranges = sorted(ranges, reverse=True, key=lambda x: x[1])
        images = sorted(
            self.files, reverse=True, key=lambda x: x.info['modified_time']
        )

        # iterate over all images and append the indexes to the ranges
        last_index = 0
        range_index = 0
        for index, image in enumerate(images):
            timestamp = image.info['modified_time']
            if timestamp < ranges[range_index][1]:
                ranges[range_index].append(last_index)
                ranges[range_index].append(index)
                last_index = index

                # skip to next possible range
                range_index = len(ranges)
                for next_range in ranges:
                    if timestamp < next_range[1]:
                        range_index = ranges.index(next_range) + 1
                if range_index >= len(ranges):
                    range_index = len(ranges) - 1
                    break
        ranges[range_index].append(last_index)
        ranges[range_index].append(len(images))

        groups = []
        for range in ranges:
            if len(range) == 4 and range[2] != range[3]:
                groups.append([range[0], images[range[2]:range[3]]])
        return groups

    @property
    def thumbnails(self):
        """ Returns the :class:`~onegov.town.model.Thumbnail` instances in this
        collection.

        """
        images = self.thumbnail_storage.ilistdirinfo(files_only=True)
        images = sorted(images, key=lambda i: i[1]['modified_time'])

        for filename, info in images:
            yield Thumbnail(filename, info)

    def get_file_by_filename(self, filename):
        """ Returns the :class:`~onegov.town.model.Image` instance with the
        given name, or None if not found.

        """
        if self.file_storage.exists(filename):
            return Image(filename)

    def get_thumbnail_by_filename(self, filename):
        """ Returns the :class:`~onegov.town.model.Thumbnail` instance with the
        given name, or None if not found.

        This method *generates* the thumbnail if it doesn't exist yet!

        """
        if not self.file_storage.exists(filename):
            return None

        if self.thumbnail_storage.exists(filename):
            return Thumbnail(filename)

        extension = filename.split('.')[-1]

        if extension not in self.thumbnail_extensions:
            return Image(filename)

        im = PIL.Image.open(self.file_storage.getsyspath(filename))
        im.thumbnail(self.thumbnail_dimension)
        im.save(
            self.thumbnail_storage.open(filename, 'wb'),
            PIL.Image.EXTENSION['.' + extension],
            quality=self.thumbnail_quality
        )

        return Thumbnail(filename)

    def delete_file_by_filename(self, filename):
        """ Deletes both the image and the thumbnail of the given filename. """

        if self.file_storage.exists(filename):
            self.file_storage.remove(filename)

        if self.thumbnail_storage.exists(filename):
            self.thumbnail_storage.remove(filename)


class Image(File):
    """ A filestorage file that points to a full image (not a thumbnail). """

    @property
    def thumbnail(self):
        return Thumbnail(self.filename)

    @property
    def path(self):
        return 'images/' + self.filename


class Thumbnail(File):
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
