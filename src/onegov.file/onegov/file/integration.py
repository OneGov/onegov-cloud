import morepath
import os.path
import shlex
import shutil
import subprocess
import yaml

from blinker import ANY
from contextlib import contextmanager
from depot.io.utils import FileIntent
from depot.manager import DepotManager
from depot.middleware import FileServeApp
from more.transaction.main import transaction_tween_factory
from morepath import App
from onegov.core.custom import json
from onegov.core.security import Private, Public
from onegov.core.utils import is_valid_yubikey, yubikey_public_id
from onegov.file.collection import FileCollection
from onegov.file.errors import AlreadySignedError
from onegov.file.errors import InvalidTokenError
from onegov.file.errors import TokenConfigurationError
from onegov.file.models import File, FileMessage
from onegov.file.sign import SigningService
from onegov.file.utils import digest, current_dir
from pathlib import Path
from sedate import utcnow
from sqlalchemy.orm import object_session
from sqlalchemy.orm.attributes import flag_modified
from tempfile import SpooledTemporaryFile


SUPPORTED_STORAGE_BACKENDS = (
    'depot.io.local.LocalFileStorage',
    'depot.io.memory.MemoryFileStorage'
)


class DepotApp(App):
    """ Provides `Depot <depot.readthedocs.io>`_ integration for
    :class:`onegov.core.framework.Framework` based applications.

    """

    custom_depot_id = None

    def configure_files(self, **cfg):
        """ Configures the file/depot integration. The following configuration
        options are accepted:

        :depot_backend: The depot backend to use. Supported values:

            * depot.io.local.LocalFileStorage
            * depot.io.memory.MemoryFileStorage

        :depot_storage_path: The storage path used by the local file storage.

            Note that the actual files are stored under a subdirectory specific
            to each application id. This is mainly to keep a handle on which
            file belongs to which application. Additionally it ensures that we
            aren't accidentally opening another application's files.

        :frontend_cache_buster: A script able to bust the frontend cache.

            Our frontend (nginx) caches the files we store in the backend and
            serves them mostly without bothering us. This can be problematic
            when the file is deleted or if it is made private. The cache
            needs to be busted in this case.

            With this configuration a script/command can be specified that
            receives the url that needs to be busted and in turn busts the
            content of this url from the cache. This pretty much depends
            on the platform this is run and on the frontend in use.

            For example, let's say our script is called 'bust-cache', this
            is the command that will be run when the cache is busted::

                sleep 5
                bust-cache id-of-the-file

            As you can see, the command is invoked with a five second delay.
            This avoids premature cache busting (before the end of the
            transaction). The command is non-blocking, so those 5 seconds
            are not counted towards the request-time.

            Frontend caches might use the domain and the full path to cache
            a file, but since we can technically have multiple domains/paths
            point to the same file we simply pass the id and let the cache
            figure out what urls need to be busted as a result.

            The script is invoked with the permissions of the user running
            the backend. If other permissions are required, use suid.

            Note that this script is optional. If omitted, the cache busting
            turns into a noop.

        :signing_services: Contains signing service configs.

            Each application gets exactly one signing service.

            This integration class will take care of instantiating the
            signing service and offer it through `self.signing_service`.

            The signing service can be used with any file, though there is
            first-class support for signing onegov.file models.

            Signing services are implemented using sublcasses of the
            :class:`onegov.file.sign.SigningService`. Each signature
            service class is configured using a single yaml file which is
            stored in the signature config path.

            By default we use the '__default__.yaml' config. Alternatively
            we can create separate configs for various application ids.

            For example, we might create a `onegov_town-govikon.yaml`, which
            would take precedence over the default config, if the application
            with the id `onegov_town-govikon` would use the signing service.

        """

        self.depot_backend = cfg.get('depot_backend')
        self.depot_storage_path = cfg.get('depot_storage_path')

        self.frontend_cache_buster = cfg.get('frontend_cache_buster')
        self.frontend_cache_bust_delay = cfg.get(
            'frontend_cache_bust_delay', 2)

        self.spawned_signing_services = {}

        if 'signing_services' in cfg:
            self.signing_services = Path(cfg['signing_services'])

        if self.depot_backend not in SUPPORTED_STORAGE_BACKENDS:
            raise RuntimeError("Depot app without valid storage backend")

        if self.depot_backend == 'depot.io.local.LocalFileStorage':
            if not os.path.isdir(self.depot_storage_path):
                raise FileNotFoundError("Depot storage path does not exist")

        if not shutil.which('gs'):
            raise RuntimeError("onegov.file requires ghostscript")

        if not shutil.which('java'):
            raise RuntimeError("onegov.file requires java")

        if self.frontend_cache_buster:

            @self.session_manager.on_update.connect_via(ANY, weak=False)
            @self.session_manager.on_delete.connect_via(ANY, weak=False)
            def on_file_change(schema, obj):
                if isinstance(obj, File):
                    self.bust_frontend_cache(obj.id)

    @property
    def bound_depot_id(self):
        return self.custom_depot_id or self.schema

    @property
    def bound_depot(self):
        assert DepotManager._default_depot == self.bound_depot_id
        return DepotManager.get()

    @property
    def bound_storage_path(self):
        return Path(self.depot_storage_path) / self.bound_depot_id

    def create_depot(self):
        config = {
            'depot.backend': self.depot_backend
        }

        if self.depot_backend.endswith('LocalFileStorage'):
            path = self.bound_storage_path

            if not path.exists():
                path.mkdir()

            config['depot.storage_path'] = str(path)

        elif self.depot_backend.endswith('MemoryFileStorage'):
            pass

        else:
            # implementing non-local file systems is going to be more
            # invloved, because we do not generate external urls yet
            raise NotImplementedError()

        DepotManager.configure(self.bound_depot_id, config)

    def bind_depot(self):
        if self.bound_depot_id not in DepotManager._depots:
            self.create_depot()

        DepotManager.set_default(self.bound_depot_id)

    def bust_frontend_cache(self, file_id):
        if not self.frontend_cache_buster:
            return

        bin = shlex.quote(self.frontend_cache_buster)
        fid = shlex.quote(file_id)
        cmd = f'sleep {self.frontend_cache_bust_delay} && {bin} {fid}'

        subprocess.Popen(cmd, close_fds=True, shell=True)

    def sign_file(self, file, signee, token, token_type='yubikey'):
        """ Signs the given file and stores metadata about that process.

        During signing the stored file is replaced with the signed version.

        For example::

            pdf = app.sign_file(pdf, 'info@example.org', 'foo')

        :param file:

            The :class:`onegov.file..File` instance to sign.

        :param signee:

            The name of the signee (should be a username).

        :param token:

            The (yubikey) token used to sign the file.

            WARNING: It is the job of the caller to ensure that the yubikey has
            the right to sign the document (i.e. that it is the right yubikey).

        :param token_type:

            They type of the passed token. Currently only 'yubikey'.

        """

        if file.signed:
            raise AlreadySignedError(file)

        if token_type == 'yubikey':
            def is_valid_token(token):
                if not getattr(self, 'yubikey_client_id', None):
                    raise TokenConfigurationError(token_type)

                return is_valid_yubikey(
                    self.yubikey_client_id,
                    self.yubikey_secret_key,
                    expected_yubikey_id=yubikey_public_id(token),
                    yubikey=token
                )
        else:
            raise NotImplementedError(f"Unknown token type: {token_type}")

        if not is_valid_token(token):
            raise InvalidTokenError(token)

        mb = 1024 ** 2
        session = object_session(file)

        with SpooledTemporaryFile(max_size=16 * mb, mode='wb') as signed:
            old_digest = digest(file.reference.file)
            request_id = self.signing_service.sign(file.reference.file, signed)
            new_digest = digest(signed)

            signed.seek(0)

            file.reference = FileIntent(
                fileobj=signed,
                filename=file.name,
                content_type=file.reference['content_type'])

        file.signature_metadata = {
            'old_digest': old_digest,
            'new_digest': new_digest,
            'signee': signee,
            'timestamp': utcnow().isoformat(),
            'request_id': request_id,
            'token': token,
            'token_type': token_type
        }

        file.signed = True

        FileMessage.log_signature(file, signee)

        session.flush()

    @property
    def signing_service_config(self):
        if not self.signing_services:
            raise RuntimeError("No signing service config path set")

        paths = (
            self.signing_services / f'{self.application_id}.yml',
            self.signing_services / f'__default__.yml',
        )

        for path in paths:
            if path.exists():
                with path.open('r') as f:
                    return yaml.load(f.read())

        raise RuntimeError(
            f"No service config found at {self.signing_services}")

    @property
    def signing_service(self):

        # it is somewhat inefficient to keep multiple instances of the same
        # service around as many services can have the same config - however
        # it prevents accidental leaks of state between applications
        if self.application_id not in self.spawned_signing_services:
            config = self.signing_service_config

            with current_dir(self.signing_services):
                self.spawned_signing_services[self.application_id] \
                    = SigningService.for_config(config)

        return self.spawned_signing_services[self.application_id]

    def clear_depot_cache(self):
        DepotManager._aliases.clear()
        DepotManager._default_depot = None
        DepotManager._depots.clear()

    @contextmanager
    def temporary_depot(self, depot_id, **configuration):
        """ Temporarily use another depot. """

        depot_backend = self.depot_backend
        depot_storage_path = self.depot_storage_path

        self.custom_depot_id = depot_id
        self.clear_depot_cache()
        self.configure_files(**configuration)
        self.bind_depot()

        yield

        self.custom_depot_id = None
        self.clear_depot_cache()
        self.configure_files(**{
            'depot_backend': depot_backend,
            'depot_storage_path': depot_storage_path
        })
        self.bind_depot()


@DepotApp.tween_factory(over=transaction_tween_factory)
def configure_depot_tween_factory(app, handler):

    assert app.has_database_connection, "This module requires a db backed app."

    def configure_depot_tween(request):
        app.bind_depot()
        return handler(request)

    return configure_depot_tween


def render_depot_file(file, request):
    return request.get_response(
        FileServeApp(file, cache_max_age=3600 * 24 * 7))


def respond_with_alt_text(reference, request):
    @request.after
    def include_alt_text(response):
        # HTTP headers are limited to ASCII, so we encode our result in
        # JSON before showing it
        response.headers.add('X-File-Note', json.dumps(
            {'note': reference.note or ''},
        ))


def respond_with_caching_header(reference, request):
    if not reference.published:
        @request.after
        def include_private_header(response):
            response.headers.add('Cache-Control', 'private')


@DepotApp.path(model=File, path='/storage/{id}')
def get_file(app, id):
    return FileCollection(app.session()).by_id(id)


@DepotApp.view(model=File, render=render_depot_file, permission=Public)
def view_file(self, request):
    respond_with_alt_text(self, request)
    respond_with_caching_header(self, request)
    return self.reference.file


@DepotApp.view(model=File, name='thumbnail', permission=Public,
               render=render_depot_file)
@DepotApp.view(model=File, name='small', permission=Public,
               render=render_depot_file)
@DepotApp.view(model=File, name='medium', permission=Public,
               render=render_depot_file)
def view_thumbnail(self, request):
    if request.view_name in ('small', 'medium'):
        size = request.view_name
    else:
        size = 'small'

    respond_with_alt_text(self, request)
    respond_with_caching_header(self, request)

    thumbnail_id = self.get_thumbnail_id(size)

    if not thumbnail_id:
        return morepath.redirect(request.link(self))

    return request.app.bound_depot.get(thumbnail_id)


@DepotApp.view(model=File, render=render_depot_file, permission=Public,
               request_method='HEAD')
def view_file_head(self, request):

    @request.after
    def set_cache(response):
        response.cache_control.max_age = 60

    return view_file(self, request)


@DepotApp.view(model=File, name='thumbnail', render=render_depot_file,
               permission=Public, request_method='HEAD')
def view_thumbnail_head(self, request):

    @request.after
    def set_cache(response):
        response.cache_control.max_age = 60

    return view_thumbnail(self, request)


@DepotApp.view(model=File, name='note', request_method='POST',
               permission=Private)
def handle_note_update(self, request):
    request.assert_valid_csrf_token()
    self.note = request.POST.get('note')

    # when updating the alt text we offer the option not to update the
    # modified date, which is helpful if the files are in modified order
    # and the order should remain when the note is changed
    if request.POST.get('keep-timestamp') in ('1', 'true', 'yes'):
        self.modified = self.modified
        flag_modified(self, 'modified')


@DepotApp.view(model=File, name='rename', request_method='POST',
               permission=Private)
def handle_rename(self, request):
    request.assert_valid_csrf_token()
    self.name = request.POST.get('name')
    self._update_metadata(filename=self.name)

    # when updating the name we offer the option not to update the
    # modified date, which is helpful if the files are in modified order
    # and the order should remain when the note is changed
    if request.POST.get('keep-timestamp') in ('1', 'true', 'yes'):
        self.modified = self.modified
        flag_modified(self, 'modified')


@DepotApp.view(model=File, request_method='DELETE', permission=Private)
def delete_file(self, request):
    """ Deletes the given file. By default the permission is
    ``Private``. An application using the framework can override this though.

    Since a DELETE can only be sent through AJAX it is protected by the
    same-origin policy. That means that we don't need to use any CSRF
    protection here.

    That being said, browser bugs and future changes in the HTML standard
    make it possible for this to happen one day. Therefore, a time-limited
    token must be passed as query parameter to this function.

    New tokens can be acquired through ``request.new_csrf_token``.

    """
    request.assert_valid_csrf_token()

    if self.signed:
        FileMessage.log_signed_file_removal(self, request.current_username)

    FileCollection(request.session).delete(self)
