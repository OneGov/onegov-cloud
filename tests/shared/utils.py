from __future__ import annotations

import dectate
import morepath
import os
import re
import shutil
import textwrap

from base64 import b64decode, b64encode
from contextlib import contextmanager
from io import BytesIO
from onegov.core.custom import json
from onegov.core.utils import Bunch, scan_morepath_modules, module_path
from onegov.ticket import TicketCollection
from PIL import Image
from random import randint
from uuid import uuid4
from xml.etree.ElementTree import tostring


from typing import overload, Any, IO, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    import pytest
    from bs4 import NavigableString, Tag
    from collections.abc import Callable, Iterator, Mapping
    from datetime import datetime
    from onegov.core.framework import Framework
    from onegov.core.orm import Base
    from onegov.reservation import Resource
    from reportlab.pdfgen.canvas import Canvas
    from sqlalchemy.orm import Session
    from tests.shared.client import Client
    from webob import Response
    from webtest.response import TestResponse

    _AppT = TypeVar('_AppT', bound=Framework)
    _ResourceT = TypeVar('_ResourceT', bound=Resource)
    _BinaryIOT = TypeVar('_BinaryIOT', bound=IO[bytes])


def get_meta(
    page: TestResponse,
    property: str,
    returns: str = 'content',
    index: int = 0
) -> str | None:
    """Searches the page for the meta tag"""
    elems = page.pyquery(f"meta[property='{property}']")
    if not elems:
        return None
    elem = elems[index]
    return elem.attrib[returns]


def encode_map_value(dictionary: Mapping[str, Any]) -> str:
    return b64encode(json.dumps(dictionary).encode('utf-8')).decode('ascii')


def decode_map_value(value: str | bytes) -> dict[str, Any]:
    return json.loads(b64decode(value).decode('utf-8'))


def open_in_browser(response: TestResponse, browser: str = 'firefox') -> None:
    if not shutil.which(browser):
        print(f'{browser} is not installed, skipping...')
        return
    path = f'/tmp/test-{str(uuid4())}.html'
    with open(path, 'w') as f:
        print(response.text, file=f)
    print(f'Opening file {path} ..')
    os.system(f'{browser} {path} &')


def open_in_excel(byte_string: IO[bytes], exe: str = 'libreoffice') -> None:
    if not shutil.which(exe):
        print(f'{exe} is not installed, skipping...')
        return

    path = '/tmp/test.xlsx'
    with open(path, 'wb') as f:
        f.write(byte_string.read())
    cmd = exe + ' --calc -n' if exe == 'libreoffice' else exe
    os.system(f'{cmd} {path} &')


def open_pdf(byte_string: IO[bytes], exe: str = 'evince') -> None:
    if not shutil.which(exe):
        print(f'{exe} is not installed, skipping...')
        return
    path = '/tmp/test.pdf'
    with open(path, 'wb') as f:
        f.write(byte_string.read())
    cmd = exe
    os.system(f'{cmd} {path} &')


@overload
def create_image(
    width: int = 50,
    height: int = 50,
    output: None = None
) -> BytesIO: ...
@overload
def create_image(
    width: int,
    height: int,
    output: _BinaryIOT
) -> _BinaryIOT: ...
@overload
def create_image(
    width: int = 50,
    height: int = 50,
    *,
    output: _BinaryIOT
) -> _BinaryIOT: ...


def create_image(
    width: int = 50,
    height: int = 50,
    output: IO[bytes] | None = None
) -> IO[bytes]:
    """ Generates a test image and returns it's file handle. """

    im = output or BytesIO()
    image = Image.new('RGBA', size=(width, height), color=(
        randint(0, 255),
        randint(0, 255),
        randint(0, 255)
    ))
    image.save(im, 'png')

    if not getattr(im, 'name', None):
        im.name = 'test.png'  # type: ignore[misc]

    im.seek(0)
    return im


def create_pdf(
    filename: str = 'simple.pdf',
    content: str = "Hello, I am a PDF document created with Python!"
) -> Canvas:

    from reportlab.pdfgen import canvas

    c = canvas.Canvas(filename)
    c.drawString(100, 750, content)
    c.save()
    return c


def assert_explicit_permissions(
    module: object,
    app_class: type[Framework]
) -> None:
    from onegov.server.utils import patch_morepath
    patch_morepath()
    morepath.autoscan()
    app_class.commit()

    for action, fn in dectate.Query('view')(app_class):
        if fn.__module__.startswith('onegov'):
            assert action.permission is not None, (
                f'{fn.__module__}.{fn.__name__} has no permission'
            )


def random_namespace() -> str:
    """ Returns a random namespace. """
    return 'test_' + uuid4().hex


def create_app(
    app_class: type[_AppT],
    request: pytest.FixtureRequest,
    enable_search: bool = False,
    reuse_filestorage: bool = True,
    use_maildir: bool = True,
    use_smsdir: bool = True,
    depot_backend: str = 'depot.io.local.LocalFileStorage',
    depot_storage_path: str | None = None,
    **kwargs: Any
) -> _AppT:

    # filestorage can be reused between tries as it is nowadays mainly (if not
    # exclusively) used by the theme compiler
    if reuse_filestorage:
        filestorage_object = request.getfixturevalue('long_lived_filestorage')
    else:
        filestorage_object = None

    if not app_class.is_committed():
        scan_morepath_modules(app_class)
        app_class.commit()

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
        identity_secret='test_identity_secret',
        csrf_secret='test_csrf_secret',
        enable_search=enable_search,
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
    app.settings.cronjobs = Bunch(enabled=False)  # type: ignore[attr-defined]

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

        app.maildir = maildir  # type: ignore[attr-defined]

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


def extract_filename_from_response(response: Response) -> str | None:
    content_disposition = response.headers.get("content-disposition")
    if content_disposition:
        filename = re.findall('filename="([^"]+)"', content_disposition)
        if filename:
            return filename[0]
    return None


def add_reservation(
    resource: _ResourceT,
    session: Session,
    start: datetime,
    end: datetime,
    email: str | None = None,
    partly_available: bool = True,
    reserve: bool = True,
    approve: bool = True,
    add_ticket: bool = True
) -> _ResourceT:
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
            with session.no_autoflush:
                tickets = TicketCollection(session)
                tickets.open_ticket(
                    handler_code='RSV', handler_id=resource_token.hex
                )
    return resource


def extract_intercooler_delete_link(client: Client, page: TestResponse) -> str:
    """ Returns the link that would be called by intercooler.js """
    delete_link = tostring(page.pyquery('a.confirm')[0]).decode('utf-8')
    href = client.extract_href(delete_link)
    assert href is not None
    return href.replace("http://localhost", "")


@contextmanager
def use_locale(model: Base, locale: str) -> Iterator[None]:
    assert model.session_manager is not None
    old_locale = model.session_manager.current_locale
    model.session_manager.current_locale = locale
    try:
        yield
    finally:
        model.session_manager.current_locale = old_locale


def href_ends_with(end: str) -> Callable[[str | None], bool]:
    """
    Returns a function that checks if the href ends with the given string.

    :argument end: The string to check for at the end of the href.

    Usage:
        response.html.find('a', href=href_ends_with('/newsletters/new'))
    """
    return lambda href: href and href.endswith(end) or False


def find_link_by_href_end(
    response: TestResponse,
    href_end: str
) -> Tag | NavigableString | None:
    """
    Returns the link that ends with the given href_end.
    :param response: a response object
    :param href_end: the string to check for at the end of the href.
    :return: link object

    """
    return response.html.find('a', href=href_ends_with(href_end))
