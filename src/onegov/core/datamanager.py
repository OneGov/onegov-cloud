from __future__ import annotations

import os
import tempfile
import transaction

from onegov.core.utils import safe_move


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from transaction.interfaces import ITransaction


class FileDataManager:

    """ Writes a file when the transaction is commited. """

    transaction_manager = transaction.manager

    def __init__(self, data: bytes, path: str, tmp_path: str | None = None):
        self.data = data
        self.path = path
        self.tmp_path = tmp_path

    @classmethod
    def write_file(
        cls,
        data: bytes,
        path: str,
        tmp_path: str | None = None
    ) -> None:
        transaction.get().join(cls(data, path, tmp_path))

    def sortKey(self) -> str:
        return 'files'

    def commit(self, transaction: ITransaction) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            self.tempfn = temp.name
            temp.write(self.data)

    def abort(self, transaction: ITransaction) -> None:
        pass

    def tpc_vote(self, transaction: ITransaction) -> None:
        if not os.path.exists(self.tempfn):
            raise ValueError(f'{self.tempfn} doesnt exist')
        if os.path.exists(self.path):
            raise ValueError('file already exists')

    def tpc_abort(self, transaction: ITransaction) -> None:
        # if another DataManager before us in the chain raises a retryable
        # error before we get to commit, we still have to execute tpc_abort
        # despite tempfn not existing yet.
        if not hasattr(self, 'tempfn'):
            return

        try:
            os.remove(self.tempfn)
        except OSError:
            pass

    def tpc_begin(self, transaction: ITransaction) -> None:
        pass

    def tpc_finish(self, transaction: ITransaction) -> None:
        safe_move(self.tempfn, self.path, tmp_dst=self.tmp_path)
