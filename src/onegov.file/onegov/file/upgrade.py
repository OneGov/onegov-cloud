""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from copy import copy
from onegov.core.upgrade import upgrade_task
from onegov.file import FileCollection
from onegov.file.attachments import get_svg_size_or_default
from onegov.file.utils import get_image_size
from PIL import Image
from sqlalchemy import Column, Text
from sqlalchemy.orm.attributes import flag_modified


@upgrade_task('Add checksum column')
def add_checksum_column(context):
    context.operations.add_column(
        'files', Column('checksum', Text, nullable=True, index=True)
    )


@upgrade_task('Add image size 3')
def add_image_size(context):
    images = FileCollection(context.session, type='image')

    for image in images.query():
        if not hasattr(image.reference, 'size'):

            # potentially dangerous and might not work with other storage
            # providers, so don't reuse unless you are sure about the
            # consequences
            image.reference._thaw()

            if image.reference.content_type == 'image/svg+xml':
                image.reference.size = get_svg_size_or_default(
                    image.reference.file
                )
            else:
                image.reference.size = get_image_size(
                    Image.open(image.reference.file)
                )

                thumbnail_metadata = copy(image.reference.thumbnail_small)
                thumbnail_metadata['size'] = get_image_size(
                    Image.open(
                        context.app.bound_depot.get(
                            image.get_thumbnail_id(size='small')
                        )
                    )
                )

                image.reference.thumbnail_small = thumbnail_metadata

            flag_modified(image, 'reference')
