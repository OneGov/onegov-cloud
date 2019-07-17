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

import bjoern
import click
import multiprocessing
import os
import signal
import shutil
import sys
import time
import traceback
import tracemalloc

from datetime import datetime
from functools import partial
from onegov.server import Config
from onegov.server import Server
from onegov.server.tracker import ResourceTracker
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from xtermcolor import colorize


RESOURCE_TRACKER = None


@click.command()
@click.option(
    '--config-file',
    '-c',
    help="Configuration file to use",
    type=click.Path(exists=True),
    default="onegov.yml"
)
@click.option(
    '--port',
    '-p',
    help="Port to bind to",
    default=8080
)
@click.option(
    '--pdb',
    help="Enable post-mortem debugging",
    default=False,
    is_flag=True
)
@click.option(
    '--tracemalloc',
    help="Enable tracemalloc",
    default=False,
    is_flag=True
)
def run(config_file, port, pdb, tracemalloc):
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
    multiprocessing.set_start_method('spawn')

    factory = partial(wsgi_factory, config_file=config_file, pdb=pdb)
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

    observer.join()
    server.join()


def wsgi_factory(config_file, pdb):
    return Server(Config.from_yaml_file(config_file), post_mortem=pdb)


class WSGIRequestMonitorMiddleware(object):
    """ Measures the time it takes to respond to a request and prints it
    at the end of the request.

    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        received = datetime.utcnow()
        received_status = None

        def local_start_response(status, headers):
            nonlocal received_status
            received_status = status

            start_response(status, headers)

        response = self.app.__call__(environ, local_start_response)

        self.log(environ, received_status, received)
        return response

    def log(self, environ, status, received):
        duration = datetime.utcnow() - received
        duration = int(round(duration.total_seconds() * 1000, 0))

        status = status.split(' ', 1)[0]
        path = f"{environ['SCRIPT_NAME']}{environ['PATH_INFO']}"
        method = environ['REQUEST_METHOD']

        template = (
            "{status} - {duration} - {method} {path} - {c:.3f} MiB ({d:+.3f})"
        )

        if status in {302, 304}:
            path = colorize(path, rgb=0x666666)  # grey
        else:
            pass  # white

        if duration > 500:
            duration = click.style(
                str(duration) + ' ms', fg='red')
        elif duration > 250:
            duration = click.style(
                str(duration) + ' ms', fg='yellow')
        else:
            duration = click.style(
                str(duration) + ' ms', fg='green')

        if method == 'POST':
            method = click.style(method, underline=True)

        RESOURCE_TRACKER.track()

        usage = RESOURCE_TRACKER.memory_usage
        delta = RESOURCE_TRACKER.memory_usage_delta

        print(template.format(
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

    def __init__(self, app_factory, host='127.0.0.1', port=8080, env={},
                 enable_tracemalloc=False):
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
    def ready(self):
        return self._ready.value == 1

    def print_memory_stats(self, signum, frame):
        print("-" * shutil.get_terminal_size((80, 20)).columns)

        RESOURCE_TRACKER.show_memory_usage()

        if tracemalloc.is_tracing():
            RESOURCE_TRACKER.show_monotonically_increasing_traces()

        print("-" * shutil.get_terminal_size((80, 20)).columns)

    def disable_systemwide_darwin_proxies(self):
        # System-wide proxy settings on darwin need to be disabled, because
        # it leads to crashes in our forked subprocess:
        # https://bugs.python.org/issue27126
        # https://bugs.python.org/issue13829
        import urllib.request
        urllib.request.proxy_bypass_macosx_sysconf = lambda host: None
        urllib.request.getproxies_macosx_sysconf = lambda: {}

    def run(self):
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
        os.system("stty sane")

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
            print(traceback.format_exc())

            # and just never start the server (but don't stop the
            # process either). this makes this work:
            # 1. save -> import error
            # 2. save corrected version -> server restarted
            while True:
                time.sleep(10.0)

        self._ready.value = 1

        print(f"started onegov server on http://{self.host}:{self.port}")
        bjoern.run()


class WsgiServer(FileSystemEventHandler):
    """ Wraps the WSGI process, providing the ability to restart the process
    and acting as an event-handler for watchdog.

    """

    def __init__(self, app_factory, host='127.0.0.1', port=8080, **kwargs):
        self.app_factory = app_factory
        self._host = host
        self._port = port
        self.kwargs = kwargs

    def spawn(self):
        return WsgiProcess(self.app_factory, self._host, self._port, {
            'ONEGOV_DEVELOPMENT': '1'
        }, **self.kwargs)

    def join(self, timeout=None):
        if self.process.is_alive():
            try:
                self.process.join(timeout)
            except AssertionError:
                pass

    def start(self):
        self.process = self.spawn()
        self.process.start()

    def restart(self):
        self.stop()
        self.start()

    def stop(self):
        self.process.terminate()

    def on_any_event(self, event):
        """ If anything of significance changed, restart the process. """

        if event.is_directory:
            return

        if event.src_path.endswith('pyc'):
            return

        if event.src_path.endswith('scss'):
            return

        if event.src_path.endswith('pt'):
            return

        if '/.git' in event.src_path:
            return

        if '/__pycache__' in event.src_path:
            return

        if '/onegov.server' in event.src_path:
            return

        if '/file-storage' in event.src_path:
            return

        if '/mails' in event.src_path:
            return

        if '/profiles' in event.src_path:
            return

        if '.webassets-cache' in event.src_path:
            return

        if 'assets/bundles' in event.src_path:
            return

        if 'onegov.sublime' in event.src_path:
            return

        if '.cache' in event.src_path:
            return

        print("changed: {}".format(event.src_path))

        self.restart()
