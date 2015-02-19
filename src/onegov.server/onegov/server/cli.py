from __future__ import print_function

import click
import multiprocessing
import os
import signal
import sys

from onegov.server.core import Server
from onegov.server.config import Config
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from wsgiref.simple_server import make_server


class WsgiProcess(multiprocessing.Process):

    def __init__(self, app_factory):
        multiprocessing.Process.__init__(self)
        self.app_factory = app_factory
        self.stdin_fileno = sys.stdin.fileno()

    def run(self):
        sys.stdin = os.fdopen(self.stdin_fileno)
        signal.signal(signal.SIGINT, lambda *args: sys.exit(0))

        os.system("stty sane")

        server = make_server('127.0.0.1', 8080, self.app_factory())
        server.serve_forever()


class WsgiServer(FileSystemEventHandler):

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
