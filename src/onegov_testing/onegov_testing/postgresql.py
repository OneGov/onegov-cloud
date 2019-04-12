import os

from subprocess import run, PIPE, DEVNULL, TimeoutExpired
from testing.common.database import get_path_of
from testing.postgresql import Postgresql as Base, SEARCH_PATHS


class Snapshot(object):
    def __init__(self, url):
        self.url = url
        self.dump = self.create_dump()

    def create_dump(self):
        return run(
            ('pg_dump', '-Fc', self.url),
            stdout=PIPE,
            check=True
        ).stdout

    def restore(self):
        try:
            run(
                ('pg_restore', '--clean', '-d', self.url),
                input=self.dump,
                stdout=DEVNULL,
                check=True,
                timeout=10
            )
        except TimeoutExpired:
            raise RuntimeError("""
                pg_restore has stalled, probably due to an idle transaction

                be sure to close all connections through either
                transaction.abort() or transaction.commit()
            """)


class Postgresql(Base):
    """ Adds snapshot support to the testing postgresql. """

    DEFAULT_KILL_TIMEOUT = 30.0

    def __init__(self, *args, **kwargs):
        self.preferred_versions = kwargs.pop('preferred_versions', [])
        super().__init__(*args, **kwargs)
        self.snapshots = []

    def initialize(self):
        self.initdb = self.settings.pop('initdb')
        if self.initdb is None:
            self.initdb = self.find_program('initdb', ['bin'])

        self.postgres = self.settings.pop('postgres')
        if self.postgres is None:
            self.postgres = self.find_program('postgres', ['bin'])

    def find_program(self, name, subdirs):
        paths = []
        for base_dir in SEARCH_PATHS:
            for subdir in subdirs:
                path = os.path.join(base_dir, subdir, name)
                if os.path.exists(path):
                    paths.append(path)

        for version in self.preferred_versions:
            for path in paths:
                if version in os.path.normpath(path).split(os.path.sep):
                    return path

        path = get_path_of(name)
        if path:
            return path

        if paths:
            return paths[0]

        raise RuntimeError("command not found: %s" % name)

    def save(self):
        self.snapshots.append(Snapshot(self.url()))
        return self.snapshots[-1]

    def undo(self, pop=True):
        if pop:
            self.snapshots.pop().restore()
        else:
            self.snapshots[-1].restore()

    def reset_snapshots(self):
        self.snapshots = []
