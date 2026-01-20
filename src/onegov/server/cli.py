""" The onegov.server can be run through the 'onegov-server' command after
installation.

Said command runs the onegov server with the given configuration file in the
foreground.

Use this **for debugging/development only**.

Example::

    onegov-server --config-file test.yml

The onegov-server will load 'onegov.yml' by default and it will restart
when any file in the current folder or any file somewhere inside './src'
changes.

Changes to omlette directories require a manual restart.

A onegov.yml file looks like this:

.. code-block:: yaml

    applications:
      - path: /apps/*
        application: my.app.TestApp
        namespace: apps
        configuration:
          allowed_hosts_expression: '^[a-z]+.apps.dev'
          dsn: postgres://username:password@localhost:5432/db
          identity_secure: false
          identity_secret: very-secret-key

    logging:
      formatters:
        simpleFormater:
          format: '%(asctime)s - %(levelname)s: %(message)s'
          datefmt: '%Y-%m-%d %H:%M:%S'

    handlers:
      console:
        class: logging.StreamHandler
        formatter: simpleFormater
        level: DEBUG
        stream: ext://sys.stdout

    loggers:
      onegov.core:
        level: DEBUG
        handlers: [console]
"""
from __future__ import annotations

import bjoern  # type:ignore[import-untyped]
import click
import multiprocessing
import os
import sentry_sdk
import shutil
import signal
import sys
import time
import traceback
import tracemalloc

from functools import partial
from importlib import import_module
from onegov.server import Config
from onegov.server import log
from onegov.server import Server
from onegov.server.tracker import ResourceTracker
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware
from time import perf_counter
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import OptExcInfo
    from _typeshed.wsgi import WSGIApplication, WSGIEnvironment, StartResponse
    from collections.abc import Callable, Iterable
    from multiprocessing.sharedctypes import Synchronized
    from types import FrameType
    from watchdog.events import FileSystemEvent


RESOURCE_TRACKER: ResourceTracker = None  # type:ignore[assignment]


@click.command()
@click.option(
    '--config-file',
    '-c',
    help='Configuration file to use',
    type=click.Path(exists=True),
    default='onegov.yml'
)
@click.option(
    '--port',
    '-p',
    help='Port to bind to',
    type=click.IntRange(min=0, max=65535),
    default=8080
)
@click.option(
    '--pdb',
    help='Enable post-mortem debugging (debug mode only)',
    default=False,
    is_flag=True
)
@click.option(
    '--tracemalloc',
    help='Enable tracemalloc (debug mode only)',
    default=False,
    is_flag=True
)
@click.option(
    '--mode',
    help='Defines the mode used to run the server cli (debug|production)',
    type=click.Choice(('debug', 'production'), case_sensitive=False),
    default='debug',
)
@click.option(
    '--sentry-dsn',
    help='Sentry DSN to use (production mode only)',
    default=None,
)
@click.option(
    '--sentry-environment',
    help='Sentry environment tag (production mode only)',
    default='testing',
)
@click.option(
    '--sentry-release',
    help='Sentry release tag (production mode only)',
    default=None,
)
@click.option(
    '--send-ppi',
    help='Allow sentry_sdk to send personally identifiable information',
    default=False,
    is_flag=True
)
@click.option(
    '--traces-sample-rate',
    help='How often should sentry_sdk send traces to the backend',
    type=click.FloatRange(min=0.0, max=1.0),
    default=0.1
)
@click.option(
    '--profiles-sample-rate',
    help='How often should sentry_sdk also send a profile with the trace',
    type=click.FloatRange(min=0.0, max=1.0),
    default=0.25
)
def run(
    config_file: str | bytes,
    port: int,
    pdb: bool,
    tracemalloc: bool,
    mode: Literal['debug', 'production'],
    sentry_dsn: str | None,
    sentry_environment: str,
    sentry_release: str | None,
    send_ppi: bool,
    traces_sample_rate: float,
    profiles_sample_rate: float
) -> None:

    """ Runs the onegov server with the given configuration file in the
    foreground.

    Use this **for debugging/development only**.

    Example::

        onegov-server --config-file test.yml

    The onegov-server will load 'onegov.yml' by default and it will restart
    when any file in the current folder or any file somewhere inside './src'
    changes.

    Changes to omlette directories require a manual restart.

    """
    # <- the docs are currently duplicated somewhat at the top of the module
    # because click does not play well with sphinx yet
    # see https://github.com/mitsuhiko/click/issues/127

    # We do not use process forking for Python's multiprocessing here, as some
    # shared libraries (namely kerberos) do not work well with forks (i.e.
    # there are hangs).
    #
    # It is also cleaner to use 'spawn' as we get a new process spawned each
    # time, which ensures that there is no residual state around that might
    # cause the first run of onegov-server to be different than any subsequent
    # runs through automated reloads.

    if mode == 'debug':
        return run_debug(config_file, port, pdb, tracemalloc)

    if sentry_dsn:
        with_sentry = True
        integrations = [
            RedisIntegration(),
            SqlalchemyIntegration(),
        ]
        # HACK: We don't want to statically depend on onegov.core
        #       from onegov.server, but our sentry integration does
        #       need to be defined there, so it knows about the internals
        #       of the application, so we use importlib.import_module
        #       to make this dependency optional, if we decide we can
        #       live with less information, we could move this out into
        #       more.sentry and import the integration from there.
        try:
            ogc_sentry = import_module('onegov.core.sentry')
            integrations.insert(0, ogc_sentry.OneGovCloudIntegration(
                # while inserting the wsgi middleware twice is not
                # harmful, we do save ourselves some static overhead
                # if we don't do it.
                with_wsgi_middleware=False
            ))
        except ImportError:
            pass

        sentry_sdk.init(
            dsn=sentry_dsn,
            release=sentry_release,
            environment=sentry_environment,
            send_default_pii=send_ppi,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=integrations)

        # somehow sentry attaches itself to the global exception hook, even if
        # we set 'install_sys_hook' to False -> so we just reset to the
        # original state before serving our application (otherwise we get each
        # error report twice)
        sys.excepthook = sys.__excepthook__
    else:
        with_sentry = False

    return run_production(config_file, port, with_sentry=with_sentry)


def run_production(
    config_file: str | bytes,
    port: int,
    with_sentry: bool
) -> None:

    # required by Bjoern
    env = {'webob.url_encoding': 'latin-1'}

    app: WSGIApplication = Server(
        config=Config.from_yaml_file(config_file),
        environ_overrides=env)

    if with_sentry:
        # NOTE: Most things should be caught at lower scopes with
        #       more detailed information by our integrations, but
        #       the SentryWsgiMiddleware also performs some bookkeeping
        #       necessary for traces and profiles to work, so we
        #       should make this the top level application wrapper
        #       We could wrap each hosted application individually
        #       instead, but then we are not measuring the overhead
        #       of this top-level application router.
        app = SentryWsgiMiddleware(app)

    log.debug(f'started onegov server on http://127.0.0.1:{port}')

    bjoern.run(app, '127.0.0.1', port, reuse_port=True)


def run_debug(
    config_file: str | bytes,
    port: int,
    pdb: bool,
    tracemalloc: bool
) -> None:

    multiprocessing.set_start_method('spawn')

    factory = partial(debug_wsgi_factory, config_file=config_file, pdb=pdb)
    server = WsgiServer(factory, port=port, enable_tracemalloc=tracemalloc)
    server.start()

    observer = Observer()
    observer.schedule(server, 'src', recursive=True)
    observer.schedule(server, '.', recursive=False)
    observer.start()

    while True:
        try:
            server.join(0.2)
        except KeyboardInterrupt:
            observer.stop()
            server.stop()
            sys.exit(0)


def debug_wsgi_factory(config_file: str | bytes, pdb: bool) -> Server:
    return Server(Config.from_yaml_file(config_file), post_mortem=pdb)


class WSGIRequestMonitorMiddleware:
    """ Measures the time it takes to respond to a request and prints it
    at the end of the request.

    """

    def __init__(self, app: WSGIApplication):
        self.app = app

    def __call__(
        self,
        environ: WSGIEnvironment,
        start_response: StartResponse
    ) -> Iterable[bytes]:

        received = perf_counter()
        received_status: str = ''

        def local_start_response(
            status: str,
            headers: list[tuple[str, str]],
            exc_info: OptExcInfo | None = None
        ) -> Callable[[bytes], object]:

            nonlocal received_status
            received_status = status

            return start_response(status, headers, exc_info)

        response = self.app(environ, local_start_response)
        self.log(environ, received_status, received)
        return response

    def log(
        self,
        environ: WSGIEnvironment,
        status: str,
        received: float
    ) -> None:

        duration_ms = (perf_counter() - received) * 1000.0
        status = status.split(' ', 1)[0]
        path = f"{environ['SCRIPT_NAME']}{environ['PATH_INFO']}"
        method = environ['REQUEST_METHOD']

        template = (
            '{status} - {duration} - {method} {path} - {c:.3f} MiB ({d:+.3f})'
        )

        if status in ('302', '304'):
            path = click.style(path, fg=(66, 66, 66))  # grey
        else:
            pass  # white

        if duration_ms > 500.0:
            duration = click.style(f'{duration_ms:.0f} ms', fg='red')
        elif duration_ms > 250.0:
            duration = click.style(f'{duration_ms:.0f} ms', fg='yellow')
        else:
            duration = click.style(f'{duration_ms:.0f} ms', fg='green')

        if method == 'POST':
            method = click.style(method, underline=True)

        RESOURCE_TRACKER.track()

        usage = RESOURCE_TRACKER.memory_usage
        delta = RESOURCE_TRACKER.memory_usage_delta

        click.echo(template.format(
            status=status,
            method=method,
            path=path,
            duration=duration,
            c=usage / 1024 / 1024,
            d=delta / 1024 / 1024
        ))


class WsgiProcess(multiprocessing.Process):
    """ Runs the WSGI reference server in a separate process. This is a debug
    process, not used in production.

    """

    _ready: Synchronized[int]

    def __init__(
        self,
        app_factory: Callable[[], WSGIApplication],
        host: str = '127.0.0.1',
        port: int = 8080,
        env: dict[str, str] | None = None,
        enable_tracemalloc: bool = False
    ):
        env = env or {}
        multiprocessing.Process.__init__(self)
        self.app_factory = app_factory
        self.host = host
        self.port = port
        self.enable_tracemalloc = enable_tracemalloc

        self._ready = multiprocessing.Value('i', 0)

        # hook up environment variables
        for key, value in env.items():
            os.environ[key] = value

        try:
            self.stdin_fileno = sys.stdin.fileno()
        except ValueError:
            pass  # in testing, stdin is not always real

    @property
    def ready(self) -> bool:
        return self._ready.value == 1

    def print_memory_stats(
        self,
        signum: int,
        frame: FrameType | None
    ) -> None:

        click.echo('-' * shutil.get_terminal_size((80, 20)).columns)

        RESOURCE_TRACKER.show_memory_usage()

        if tracemalloc.is_tracing():
            RESOURCE_TRACKER.show_monotonically_increasing_traces()

        click.echo('-' * shutil.get_terminal_size((80, 20)).columns)

    def disable_systemwide_darwin_proxies(self):  # type:ignore
        # System-wide proxy settings on darwin need to be disabled, because
        # it leads to crashes in our forked subprocess:
        # https://bugs.python.org/issue27126
        # https://bugs.python.org/issue13829
        import urllib.request
        urllib.request.proxy_bypass_macosx_sysconf = lambda host: None  # type:ignore[attr-defined]
        urllib.request.getproxies_macosx_sysconf = dict  # type:ignore[attr-defined]

    def run(self) -> None:
        # use the parent's process stdin to be able to provide pdb correctly
        if hasattr(self, 'stdin_fileno'):
            sys.stdin = os.fdopen(self.stdin_fileno)

        # when pressing ctrl+c exit immediately
        signal.signal(signal.SIGINT, lambda *args: sys.exit(0))

        # when pressing ctrl+t show the memory usage of the process
        if hasattr(signal, 'SIGINFO'):
            signal.signal(signal.SIGINFO, self.print_memory_stats)

        # reset the tty every time, fixing problems that might occur if
        # the process is restarted during a pdb session
        os.system('stty sane')  # nosec

        try:
            if sys.platform == 'darwin':
                self.disable_systemwide_darwin_proxies()

            global RESOURCE_TRACKER
            RESOURCE_TRACKER = ResourceTracker(
                enable_tracemalloc=self.enable_tracemalloc)

            wsgi_application = WSGIRequestMonitorMiddleware(self.app_factory())
            bjoern.listen(wsgi_application, self.host, self.port)
        except Exception:
            # if there's an error, print it
            click.echo(traceback.format_exc())

            # and just never start the server (but don't stop the
            # process either). this makes this work:
            # 1. save -> import error
            # 2. save corrected version -> server restarted
            while True:
                time.sleep(10.0)

        self._ready.value = 1

        click.echo(f'started onegov server on http://{self.host}:{self.port}')
        bjoern.run()


class WsgiServer(FileSystemEventHandler):
    """ Wraps the WSGI process, providing the ability to restart the process
    and acting as an event-handler for watchdog.

    """

    def __init__(
        self,
        app_factory: Callable[[], WSGIApplication],
        host: str = '127.0.0.1',
        port: int = 8080,
        **kwargs: Any
    ):
        self.app_factory = app_factory
        self._host = host
        self._port = port
        self.kwargs = kwargs

    def spawn(self) -> WsgiProcess:
        return WsgiProcess(self.app_factory, self._host, self._port, {
            'ONEGOV_DEVELOPMENT': '1',
            'CHAMELEON_CACHE': '.chameleon_cache'
        }, **self.kwargs)

    def join(self, timeout: float | None = None) -> None:
        try:
            self.process.join(timeout)
        except Exception:
            # ignore errors such as not yet started, process already finished
            # or already closed process objects - it's used for debug anyway
            log.warning('Could not join')

    def start(self) -> None:
        self.process = self.spawn()
        self.process.start()

    def restart(self) -> None:
        self.stop(block=True)
        self.start()

    def stop(self, block: bool = False) -> None:
        self.process.terminate()
        if block:
            self.join()

    def on_any_event(self, event: FileSystemEvent) -> None:
        """ If anything of significance changed, restart the process. """

        if getattr(event, 'event_type', None) in ('opened', 'closed_no_write'):
            return

        src_path = event.src_path
        assert isinstance(src_path, str)

        if 'tests/' in src_path:
            return

        if event.is_directory:
            return

        if src_path.endswith('pyc'):
            return

        if src_path.endswith('scss'):
            return

        if src_path.endswith('pt'):
            return

        if src_path.endswith('.rdb'):
            return

        if src_path.endswith('.md'):
            return

        if '/.testmondata' in src_path:
            return

        if '/.git' in src_path:
            return

        if '/__pycache__' in src_path:
            return

        if '/onegov.server' in src_path:
            return

        if '/file-storage' in src_path:
            return

        if '/mails' in src_path:
            return

        if '/profiles' in src_path:
            return

        if '.webassets-cache' in src_path:
            return

        if 'assets/bundles' in src_path:
            return

        if 'onegov.sublime' in src_path:
            return

        if '.cache' in src_path:
            return

        if src_path.endswith('~'):
            return

        if '.tmp.' in src_path:
            return

        click.echo(f'changed: {src_path}')

        self.restart()
