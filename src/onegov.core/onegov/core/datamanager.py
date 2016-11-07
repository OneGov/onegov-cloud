import os
import tempfile
import transaction

from onegov.core import log


class MailDataManager(object):
    """ Takes a postman and an envelope and sends it when the transaction
    is commited.

    Since we can't really know if a mail can be sent until it happens, we
    simply log an exception if the sending failed.

    """

    transaction_manager = transaction.manager

    def __init__(self, postman, envelope):
        self.postman = postman
        self.envelope = envelope

    @classmethod
    def send_email(cls, postman, envelope):
        transaction.get().join(cls(postman, envelope))

    def sortKey(self):
        return 'mails'

    def commit(self, transaction):
        try:
            self.postman.send(self.envelope)
        except Exception:
            log.exception("Failed to send e-mail")

    def abort(self, transaction):
        pass

    def tpc_vote(self, transaction):
        pass

    def tpc_abort(self, transaction):
        pass

    def tpc_begin(self, transaction):
        pass

    def tpc_finish(self, transaction):
        pass


class FileDataManager(object):

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
        os.rename(self.tempfn, self.path)
