from onegov.core.custom import json
import os
import shutil
import re

import dectate
import morepath
import textwrap

from io import BytesIO
from onegov.core.utils import Bunch, scan_morepath_modules, module_path
from PIL import Image
from random import randint
from uuid import uuid4
from base64 import b64decode, b64encode

from onegov.ticket import TicketCollection


def get_meta(page, property, returns='content', index=0):
    """Searches the page for the meta tag"""
    elems = page.pyquery(f"meta[property='{property}']")
    if not elems:
        return None
    elem = elems[index]
    return elem.attrib[returns]


def encode_map_value(dictionary):
    return b64encode(json.dumps(dictionary).encode('utf-8')).decode('ascii')


def decode_map_value(value):
    return json.loads(b64decode(value).decode('utf-8'))


def open_in_browser(response, browser='firefox'):
    if not shutil.which(browser):
        print(f'{browser} is not installed, skipping...')
        return
    path = f'/tmp/test-{str(uuid4())}.html'
    with open(path, 'w') as f:
        print(response.text, file=f)
    # os.system(f'{browser} {path} &')
    print(f'Opening file {path} ..')
    os.system(f'{browser} {path} &')


def open_in_excel(byte_string, exe='libreoffice'):
    if not shutil.which(exe):
        print(f'{exe} is not installed, skipping...')
        return

    path = '/tmp/test.xlsx'
    with open(path, 'wb') as f:
        f.write(byte_string.read())
    cmd = exe + ' --calc -n' if exe == 'libreoffice' else exe
    os.system(f'{cmd} {path} &')


def open_pdf(byte_string, exe='evince'):
    if not shutil.which(exe):
        print(f'{exe} is not installed, skipping...')
        return
    path = '/tmp/test.pdf'
    with open(path, 'wb') as f:
        f.write(byte_string.read())
    cmd = exe
    os.system(f'{cmd} {path} &')


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


def create_pdf(filename='simple.pdf'):
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(filename)
    c.drawString(100, 750,
                 "Hello, I am a PDF document created with Python!")
    c.save()
    return c


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
               reuse_filestorage=True, use_maildir=True, use_smsdir=True,
               depot_backend='depot.io.local.LocalFileStorage',
               depot_storage_path=None, **kwargs):

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

    if depot_backend == 'depot.io.local.LocalFileStorage':
        if not depot_storage_path:
            depot_storage_path = request.getfixturevalue('temporary_directory')

    temporary_path = request.getfixturevalue('temporary_path')
    signing_services = (temporary_path / 'signing-services')
    signing_services.mkdir()

    cert_file = module_path('tests.shared', 'fixtures/self-signed.crt')
    cert_key = module_path('tests.shared', 'fixtures/self-signed.key')

    with (signing_services / '__default__.yml').open('w') as f:
        f.write(textwrap.dedent(f"""
            name: swisscom_ais
            parameters:
                customer: foo
                key_static: bar
                cert_file: {cert_file}
                cert_key: {cert_key}
        """))

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
        redis_url=request.getfixturevalue('redis_url'),
        yubikey_client_id='foo',
        yubikey_secret_key='dGhlIHdvcmxkIGlzIGNvbnRyb2xsZWQgYnkgbGl6YXJkcyE=',
        signing_services=str(signing_services),
        **kwargs
    )

    app.set_application_id(app.namespace + '/test')
    app.clear_request_cache()

    if hasattr(app, 'bind_depot'):
        app.bind_depot()

    # cronjobs leave lingering sessions open, in real life this is not a
    # problem, but in testing it leads to connection pool exhaustion
    app.settings.cronjobs = Bunch(enabled=False)

    if use_maildir:
        maildir = request.getfixturevalue('maildir')

        app.mail = {
            'marketing': {
                'directory': maildir,
                'sender': 'mails@govikon.ch'
            },
            'transactional': {
                'directory': maildir,
                'sender': 'mails@govikon.ch'
            }
        }

        app.maildir = maildir

    if use_smsdir:
        smsdir = request.getfixturevalue('smsdir')
        app.sms = {
            'directory': smsdir,
            'sender': 'Govikon',
            'user': 'test',
            'password': 'test'
        }
        app.sms_directory = smsdir

    return app


def extract_filename_from_response(response):
    content_disposition = response.headers.get("content-disposition")
    if content_disposition:
        filename = re.findall('filename="([^"]+)"', content_disposition)
        if filename:
            return filename[0]
    return None


def add_reservation(
    resource,
    client,
    start,
    end,
    email=None,
    partly_available=True,
    reserve=True,
    approve=True,
    add_ticket=True
):
    if not email:
        email = f'{resource.name}@example.org'

    allocation = resource.scheduler.allocate(
        (start, end),
        partly_available=partly_available,
    )[0]

    if reserve:
        resource_token = resource.scheduler.reserve(
            email,
            (allocation.start, allocation.end),
        )

    if reserve and approve:
        resource.scheduler.approve_reservations(resource_token)
        if add_ticket:
            with client.app.session().no_autoflush:
                tickets = TicketCollection(client.app.session())
                tickets.open_ticket(
                    handler_code='RSV', handler_id=resource_token.hex
                )
    return resource
