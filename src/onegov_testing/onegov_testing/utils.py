import dectate
import morepath

from io import BytesIO
from onegov.core.utils import Bunch, scan_morepath_modules
from PIL import Image
from random import randint
from uuid import uuid4


def create_image(width=50, height=50, output=None):
    """ Generates a test image and returns it's file handle. """

    im = output or BytesIO()
    image = Image.new('RGBA', size=(width, height), color=(
        randint(0, 255),
        randint(0, 255),
        randint(0, 255)
    ))
    image.save(im, 'png')

    if not getattr(im, 'name', None):
        im.name = 'test.png'

    im.seek(0)
    return im


def assert_explicit_permissions(module, app_class):
    morepath.autoscan()
    app_class.commit()

    for action, fn in dectate.Query('view')(app_class):
        if fn.__module__.startswith('onegov'):
            assert action.permission is not None, (
                f'{fn.__module__}.{fn.__name__} has no permission'
            )


def random_namespace():
    """ Returns a random namespace. """
    return 'test_' + uuid4().hex


def create_app(app_class, request, use_elasticsearch=False,
               reuse_filestorage=True, use_smtp=True,
               depot_backend='depot.io.memory.MemoryFileStorage',
               depot_storage_path=None):

    # filestorage can be reused between tries as it is nowadays mainly (if not
    # exclusively) used by the theme compiler
    if reuse_filestorage:
        filestorage_object = request.getfixturevalue('long_lived_filestorage')
    else:
        filestorage_object = None

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
        filestorage='fs.osfs.OSFS',
        filestorage_object=filestorage_object,
        depot_backend=depot_backend,
        depot_storage_path=depot_storage_path,
        identity_secure=False,
        enable_elasticsearch=use_elasticsearch,
        elasticsearch_hosts=elasticsearch_hosts,
        redis_url=request.getfixturevalue('redis_url')
    )

    app.set_application_id(app.namespace + '/test')
    app.clear_request_cache()

    if hasattr(app, 'bind_depot'):
        app.bind_depot()

    # cronjobs leave lingering sessions open, in real life this is not a
    # problem, but in testing it leads to connection pool exhaustion
    app.settings.cronjobs = Bunch(enabled=False)

    if use_smtp:
        smtp = request.getfixturevalue('smtp')

        app.mail = {
            'marketing': {
                'host': smtp.address[0],
                'port': smtp.address[1],
                'force_tls': False,
                'username': None,
                'password': None,
                'use_directory': False,
                'sender': 'mails@govikon.ch'
            },
            'transactional': {
                'host': smtp.address[0],
                'port': smtp.address[1],
                'force_tls': False,
                'username': None,
                'password': None,
                'use_directory': False,
                'sender': 'mails@govikon.ch'
            }
        }

        app.smtp = smtp

    return app
