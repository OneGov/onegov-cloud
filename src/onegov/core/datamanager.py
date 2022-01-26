import os
import tempfile
import transaction

from onegov.core.utils import safe_move


class FileDataManager:

    """ Writes a file when the transaction is commited. """

    transaction_manager = transaction.manager

    def __init__(self, data, path):
        self.data = data
        self.path = path

    @classmethod
    def write_file(cls, data, path):
        transaction.get().join(cls(data, path))

    def sortKey(self):
        return 'files'

    def commit(self, transaction):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            self.tempfn = temp.name
            temp.write(self.data)

    def abort(self, transaction):
        pass

    def tpc_vote(self, transaction):
        if not os.path.exists(self.tempfn):
            raise ValueError('%s doesnt exist' % self.tempfn)
        if os.path.exists(self.path):
            raise ValueError('file already exists')

    def tpc_abort(self, transaction):
        try:
            os.remove(self.tempfn)
        except OSError:
            pass

    def tpc_begin(self, transaction):
        pass

    def tpc_finish(self, transaction):
        safe_move(self.tempfn, self.path)
