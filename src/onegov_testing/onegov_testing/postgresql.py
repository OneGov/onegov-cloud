from testing.postgresql import Postgresql as Base
from subprocess import run, PIPE, DEVNULL, TimeoutExpired


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.snapshots = []

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
