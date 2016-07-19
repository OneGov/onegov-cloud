import onegov.core

from io import BytesIO
from PIL import Image
from random import randint
from unittest.mock import patch


def create_image(width=50, height=50):
    """ Generates a test image and returns it's file handle. """

    im = BytesIO()
    image = Image.new('RGBA', size=(width, height), color=(
        randint(0, 255),
        randint(0, 255),
        randint(0, 255)
    ))
    image.save(im, 'png')
    im.name = 'test.png'
    im.seek(0)
    return im


def assert_explicit_permissions(module, app_class):
    with patch('morepath.view.ViewRegistry.register_view') as register_view:

        import morepath

        morepath.scan(onegov.core)
        morepath.scan(module)
        app_class.commit()

        # make sure that all registered views have an explicit permission
        for call in register_view.call_args_list:
            view = call[0][1]
            permission = call[0][4]

            if view.__module__.startswith('onegov'):

                assert permission is not None, (
                    'view {}.{} has no permission'.format(
                        module, view.__name__))
