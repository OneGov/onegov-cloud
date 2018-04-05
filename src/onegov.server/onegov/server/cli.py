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

import click
import gc
import multiprocessing
import os
import psutil
import signal
import sys
import time
import traceback
import tracemalloc

from datetime import datetime
from onegov.server import Server
from onegov.server import Config
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from wsgiref.simple_server import make_server, WSGIRequestHandler
from xtermcolor import colorize


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
    '--tracemalloc-type',
    help="Set the tracemalloc type",
    default='lineno',
    type=click.Choice(('filename', 'lineno', 'traceback'))
)
@click.option(
    '--tracemalloc-frames',
    help="Number of frames tracemalloc captures",
    default=2,
    type=int
)
@click.option(
    '--tracemalloc-top',
    help="Number of traces to show (in order of size)",
    default=5,
    type=int
)
def run(config_file, port, pdb,
        tracemalloc_type, tracemalloc_frames, tracemalloc_top):
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

    def wsgi_factory():
        return Server(Config.from_yaml_file(config_file), post_mortem=pdb)

    server = WsgiServer(
        wsgi_factory,
        port=port,
        tracemalloc_type=tracemalloc_type,
        tracemalloc_frames=tracemalloc_frames,
        tracemalloc_top=tracemalloc_top
    )

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


def current_memory_usage():
    return psutil.Process(os.getpid()).memory_info().rss


LAST_MEMORY_USAGE = current_memory_usage()


class CustomWSGIRequestHandler(WSGIRequestHandler):
    """ Measures the time it takes to respond to a request and prints it
    at the end of the request.

    """

    def parse_request(self):
        self._started = datetime.utcnow()
        self._memory = current_memory_usage()

        return WSGIRequestHandler.parse_request(self)

    def log_request(self, status, bytes):
        status = int(status)

        duration = datetime.utcnow() - self._started
        duration = int(round(duration.total_seconds() * 1000, 0))

        method = self.command
        path = self.path

        template = "{status} - {duration} - {method} {path} {c:.3f} ({d:+.3f})"

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

        global LAST_MEMORY_USAGE
        current_usage = current_memory_usage()

        print(template.format(
            status=status,
            method=method,
            path=path,
            duration=duration,
            c=current_usage / 1024 / 1024,
            d=(current_usage - LAST_MEMORY_USAGE) / 1024 / 1024
        ))

        LAST_MEMORY_USAGE = current_usage


class WsgiProcess(multiprocessing.Process):
    """ Runs the WSGI reference server in a separate process. This is a debug
    process, not used in production.

    """

    def __init__(self, app_factory, host='127.0.0.1', port=8080,
                 tracemalloc_type='filename',
                 tracemalloc_frames=2,
                 tracemalloc_top=10):

        multiprocessing.Process.__init__(self)
        self.app_factory = app_factory

        self.host = host

        # if the port is set to 0, a random port will be selected by the os
        self._port = port
        self._actual_port = multiprocessing.Value('i', port)
        self._ready = multiprocessing.Value('i', 0)

        # memory usage over time
        self.memory_usage = [current_memory_usage()]
        self.memory_usage_max_count = 10

        # tracemalloc
        self.snapshots = []
        self.tracemalloc_type = tracemalloc_type
        self.tracemalloc_frames = tracemalloc_frames
        self.tracemalloc_top = tracemalloc_top

        try:
            self.stdin_fileno = sys.stdin.fileno()
        except ValueError:
            pass  # in testing, stdin is not always real

    @property
    def ready(self):
        return self._ready.value == 1

    @property
    def port(self):
        return self._actual_port.value

    def take_tracemalloc_snapshot(self):

        if not tracemalloc.is_tracing():
            tracemalloc.start(self.tracemalloc_frames)

        # reduces noise
        gc.collect()

        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append(snapshot)

        return snapshot

    def compare_snapshots(self, prev, curr):

        # exclude debugging tools
        excluded = ('tracemalloc', 'linecache', 'objgraph', 'server/cli')

        filters = [
            tracemalloc.Filter(
                inclusive=False,
                filename_pattern=f'*{ex}*',
                all_frames=False
            ) for ex in excluded
        ]

        prev = prev.filter_traces(filters)
        curr = curr.filter_traces(filters)

        stats = curr.compare_to(prev, self.tracemalloc_type)
        stats.sort(key=lambda s: s.size_diff, reverse=True)

        for stat in stats[:self.tracemalloc_top]:
            delta_blocks = stat.count_diff
            delta_kibyte = stat.size_diff / 1024

            print(f"Δ size: {delta_kibyte} KiB | Δ blocks: {delta_blocks}")

            for line in stat.traceback.format():
                print(colorize(line, rgb=0x666666))

    def print_memory_stats(self, signum, frame):

        # these are only installed in the development environment
        import objgraph
        import plotille

        if len(self.memory_usage) == self.memory_usage_max_count:
            self.memory_usage.pop(0)

        self.memory_usage.append(current_memory_usage())
        total_memory = self.memory_usage[-1] / 1024 / 1024

        if len(self.memory_usage) > 1:
            delta = (self.memory_usage[-1] - self.memory_usage[-2]) / 1024
        else:
            delta = 0

        print(f"Total memory used: {total_memory:.2f} mb (Δ {delta}KiB)")
        print()
        print("Memory usage graph:")
        x = tuple(range(len(self.memory_usage)))
        y = tuple(b / 1024 for b in self.memory_usage)
        print(plotille.plot(
            X=x,
            Y=y,
            height=15,
            width=50,
            lc='blue',
            Y_label='KiB',
            X_label='invocations'
        ))
        print()
        print("Most common types:")
        objgraph.show_most_common_types(limit=10)
        print()
        print("Growth since last invocation:")
        objgraph.show_growth(limit=10)
        print()

        if not self.snapshots:
            print("No tracemalloc snapshots yet, creating first one.")
            print()
            self.take_tracemalloc_snapshot()
        else:
            print("Tracemalloc growth:")
            prev, curr = self.snapshots[-1], self.take_tracemalloc_snapshot()
            self.compare_snapshots(prev, curr)

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

            server = make_server(
                self.host, self.port, self.app_factory(),
                handler_class=CustomWSGIRequestHandler)
        except Exception:
            # if there's an error, print it
            print(traceback.format_exc())

            # and just never start the server (but don't stop the
            # process either). this makes this work:
            # 1. save -> import error
            # 2. save corrected version -> server restarted
            while True:
                time.sleep(10.0)

        self._actual_port.value = server.socket.getsockname()[1]
        self._ready.value = 1

        print("started onegov server on http://{}:{}".format(
            self.host, self.port))

        server.serve_forever()


class WsgiServer(FileSystemEventHandler):
    """ Wraps the WSGI process, providing the ability to restart the process
    and acting as an event-handler for watchdog.

    """

    def __init__(self, app_factory, host='127.0.0.1', port=8080, **extra):
        self.app_factory = app_factory
        self._host = host
        self._port = port
        self._extra = extra

    def spawn(self):
        return WsgiProcess(
            self.app_factory, self._host, self._port, **self._extra)

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
