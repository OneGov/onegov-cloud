import onegov.core

from io import BytesIO
from PIL import Image
from unittest.mock import patch


def create_image():
    """ Generates a test image and returns it's file handle. """

    im = BytesIO()
    image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
    image.save(im, 'png')
    im.name = 'test.png'
    im.seek(0)
    return im


def assert_explicit_permissions(module):

    # support morepath 0.12 until 0.13 is out
    try:
        return assert_explicit_permissions_old(module)
    except ImportError:
        return assert_explicit_permissions_new(module)


def assert_explicit_permissions_new(module):
    with patch('morepath.view.ViewRegistry.register_view') as register_view:

        import morepath

        morepath.scan(onegov.core)
        morepath.scan(module)
        morepath.autocommit()

        # make sure that all registered views have an explicit permission
        for call in register_view.call_args_list:
            view = call[0][1]
            permission = call[0][4]

            if view.__module__.startswith('onegov'):
                assert permission is not None, (
                    'view {}.{} has no permission'.format(
                        module, view.__name__))


def assert_explicit_permissions_old(module):

    from morepath import setup

    with patch('morepath.directive.register_view') as register_view:

        config = setup()
        config.scan(onegov.core)
        config.scan(module)
        config.commit()

        module_name = module.__name__

        # make sure that all registered views have an explicit permission
        for call in register_view.call_args_list:
            view = call[0][2]
            module = view.__venusian_callbacks__[None][0][1]
            permission = call[0][5]

            if module.startswith(module_name) and permission is None:
                assert permission is not None, (
                    'view {}.{} has no permission'.format(
                        module, view.__name__))
