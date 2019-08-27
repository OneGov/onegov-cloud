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

    def bind_connection(self, transaction, connection):
        assert 'mail_connection' not in transaction.extension

        def after_commit_hook(*args):
            connection.quit()

        transaction.addAfterCommitHook(after_commit_hook)
        transaction.extension['mail_connection'] = connection

    def open_connection(self):
        connection = self.postman.transport(
            self.postman.host,
            self.postman.port,
            **self.postman.options
        )

        connection.ehlo()

        for item in self.postman.middlewares:
            item(connection)

        return connection

    def commit(self, transaction):
        if 'mail_connection' not in transaction.extension:
            self.bind_connection(transaction, self.open_connection())

        try:
            self.postman.deliver(
                transaction.extension['mail_connection'],
                self.envelope
            )
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
