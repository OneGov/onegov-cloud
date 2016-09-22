import morepath

from onegov.core.utils import Bunch, scan_morepath_modules
from io import BytesIO
from PIL import Image
from random import randint
from unittest.mock import patch
from uuid import uuid4


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
    morepath.autoscan()
    app_class.commit()

    with patch('morepath.view.ViewRegistry.register_view') as register_view:

        # make sure that all registered views have an explicit permission
        for call in register_view.call_args_list:
            view = call[0][1]
            permission = call[0][4]

            if view.__module__.startswith('onegov'):

                assert permission is not None, (
                    'view {}.{} has no permission'.format(
                        module, view.__name__))


def random_namespace():
    """ Returns a random namespace. """
    return 'test_' + uuid4().hex


def create_app(app_class, request, use_elasticsearch=False):

    if not app_class.is_committed():
        scan_morepath_modules(app_class)
        app_class.commit()

    if use_elasticsearch:
        elasticsearch_hosts = [
            request.getfixturevalue('es_url')
        ]
    else:
        elasticsearch_hosts = []

    app = app_class()
    app.namespace = random_namespace()
    app.configure_application(
        dsn=request.getfixturevalue('postgres_dsn'),
        filestorage='fs.memoryfs.MemoryFS',
        depot_backend='depot.io.memory.MemoryFileStorage',
        identity_secure=False,
        disable_memcached=True,
        enable_elasticsearch=use_elasticsearch,
        elasticsearch_hosts=elasticsearch_hosts
    )

    app.set_application_id(app.namespace + '/test')
    app.bind_depot()

    # cronjobs leave lingering sessions open, in real life this is not a
    # problem, but in testing it leads to connection pool exhaustion
    app.settings.cronjobs = Bunch(enabled=False)

    smtp = request.getfixturevalue('smtp')

    app.mail_host, app.mail_port = smtp.address
    app.mail_sender = 'mails@govikon.ch'
    app.mail_force_tls = False
    app.mail_username = None
    app.mail_password = None
    app.mail_use_directory = False
    app.smtp = smtp

    return app
