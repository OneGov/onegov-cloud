from __future__ import print_function

import click
import multiprocessing
import os
import signal
import sys

from datetime import datetime
from onegov.server.core import Server
from onegov.server.config import Config
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from wsgiref.simple_server import make_server, WSGIRequestHandler


class CustomWSGIRequestHandler(WSGIRequestHandler):
    """ Measures the time it takes to respond to a request and prints it
    at the end of the request.

    """

    def parse_request(self):
        self._started = datetime.utcnow()

        return super(CustomWSGIRequestHandler, self).parse_request()

    def log_request(self, status, bytes):
        duration = datetime.utcnow() - self._started
        duration = int(round(duration.total_seconds() * 1000, 0))

        print("{} - {} {} - {} ms - {} bytes".format(
            status, self.command, self.path, duration, bytes))


class WsgiProcess(multiprocessing.Process):
    """ Runs the WSGI reference server in a separate process. """

    def __init__(self, app_factory):
        multiprocessing.Process.__init__(self)
        self.app_factory = app_factory
        self.stdin_fileno = sys.stdin.fileno()

    def run(self):
        # use the parent's process stdin to be able to provide pdb correctly
        sys.stdin = os.fdopen(self.stdin_fileno)

        # when pressing ctrl+c exit immediately
        signal.signal(signal.SIGINT, lambda *args: sys.exit(0))

        # reset the tty every time, fixing problems that might occur if
        # the process is restarted during a pdb session
        os.system("stty sane")

        print("starting onegov server on https://127.0.0.1:8080")

        server = make_server(
            '127.0.0.1', 8080, self.app_factory(),
            handler_class=CustomWSGIRequestHandler)

        server.serve_forever()


class WsgiServer(FileSystemEventHandler):
    """ Wraps the WSGI process, providing the ability to restart the process
    and acting as an event-handler for watchdog.

    """

    def __init__(self, app_factory):
        self.app_factory = app_factory

    def spawn(self):
        return WsgiProcess(self.app_factory)

    def join(self, timeout=None):
        if self.process.is_alive():
            self.process.join(timeout)

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

        if event.src_path.endswith('pyc'):
            return

        if '/.git' in event.src_path:
            return

        if '/__pycache__' in event.src_path:
            return

        if '/onegov.server' in event.src_path:
            return

        self.restart()


@click.command()
@click.option(
    '--config-file',
    '-c',
    help="Configuration file to use",
    type=click.Path(exists=True),
    default="onegov.yml"
)
def run(config_file):
    """ Runs the onegov server with the given configuration file in the
    foreground.

    Use this *for debugging/development only*.

    Example::

        onegov-server --config-file test.yml

    The onegov-server will load 'onegov.yml' by default and it will restart
    when any file in the current folder or any of its subfolders changes.
    """

    def wsgi_factory():
        return Server(Config.from_yaml_file(config_file))

    server = WsgiServer(wsgi_factory)
    server.start()

    observer = Observer()
    observer.schedule(server, '.', recursive=True)
    observer.start()

    while True:
        try:
            server.join(1.0)
        except KeyboardInterrupt:
            observer.stop()
            server.stop()
            sys.exit(0)

    observer.join()
    server.join()
