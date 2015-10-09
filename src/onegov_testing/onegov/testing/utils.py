import morepath
import onegov.core

from importlib import import_module
from io import BytesIO
from morepath import setup
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


def morepath_modules(cls):
    """ Returns all morepath modules which should be scanned for the given
    morepath application class.

    We can't reliably know the actual morepath modules that
    need to be scanned, which is why we assume that each module has
    one namespace (like 'more.transaction').

    """
    for base in cls.__mro__:
        if not issubclass(base, morepath.App):
            continue

        if base is morepath.App:
            continue

        module = '.'.join(base.__module__.split('.')[:2])

        if module.startswith('test'):
            continue

        yield module


def scan_morepath_modules(cls, config):
    """ Tries to scann all the morepath modules required for the given
    application class. This is not guaranteed to stay reliable as there is
    no sure way to discover all modules required by the application class.

    """
    for module in sorted(morepath_modules(cls)):
        config.scan(import_module(module))
