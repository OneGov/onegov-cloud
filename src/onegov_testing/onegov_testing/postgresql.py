from testing.postgresql import Postgresql as Base
from subprocess import run, PIPE, DEVNULL


class Snapshot(object):
    def __init__(self, url):
        self.url = url
        self.restored = False
        self.dump = self.create_dump()

    def create_dump(self):
        process = run(('pg_dump', self.url, '--clean'), stdout=PIPE)
        process.check_returncode()

        return process.stdout

    def restore(self):
        process = run(('psql', self.url), input=self.dump, stdout=DEVNULL)
        process.check_returncode()

        self.restored = True


class Postgresql(Base):
    """ Adds snapshot support to the testing postgresql. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.snapshots = []

    def save(self):
        self.snapshots.append(Snapshot(self.url()))
        return self.snapshots[-1]

    def undo(self):
        # snapshots can be restored outside this stack
        self.snapshots = [s for s in self.snapshots if not s.restored]
        self.snapshots.pop().restore()

    def reset_snapshots(self):
        self.snapshots = []
