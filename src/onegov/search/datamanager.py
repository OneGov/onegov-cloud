from __future__ import annotations

import transaction

from onegov.search import log
from weakref import WeakKeyDictionary


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.search.indexer import Indexer, Task
    from sqlalchemy.orm import Session
    from transaction.interfaces import ITransaction


class TaskQueue(list['Task']):
    def __init__(self, max_size: int = 0) -> None:
        super().__init__()
        self.max_size = max_size

    def append(self, value: Task) -> None:
        if self.max_size and len(self) >= self.max_size:
            log.error('The orm event translator queue is full!')
            return
        super().append(value)

    # NOTE: Disallow extend/insert/__setitem__
    __setitem__ = extend = insert = None  # type: ignore[assignment]


_DATAMANAGERS: WeakKeyDictionary[Session, IndexerDataManager]
_DATAMANAGERS = WeakKeyDictionary()


class IndexerDataManager:
    """ Flushes pending indexing tasks to the database. """

    transaction_manager = transaction.manager

    queue: TaskQueue | None
    session: Session | None
    indexer: Indexer | None

    def __init__(
        self,
        session: Session,
        indexer: Indexer,
        max_queue_size: int = 0
    ) -> None:
        self.session = session
        self.indexer = indexer
        self.queue = TaskQueue(max_queue_size)
        transaction.get().join(self)
        _DATAMANAGERS[session] = self

    @classmethod
    def get_queue(
        cls,
        session: Session | None,
        indexer: Indexer,
        max_queue_size: int = 0
    ) -> TaskQueue | None:

        if session is None:
            return None

        instance = _DATAMANAGERS.get(session)
        if instance is None:
            instance = cls(session, indexer, max_queue_size)

        return instance.queue

    def _finish(self) -> None:
        assert self.session is not None
        assert self.queue is not None
        del _DATAMANAGERS[self.session]
        self.queue.clear()
        self.session = self.indexer = self.queue = None

    def sortKey(self) -> str:
        # we want to sort close to the end but before zope.sqlalchemy
        return '~indexer'

    def commit(self, transaction: ITransaction) -> None:
        pass

    def abort(self, transaction: ITransaction) -> None:
        if self.session is not None:
            self._finish()

    def tpc_begin(self, transaction: ITransaction) -> None:
        pass

    def tpc_vote(self, transaction: ITransaction) -> None:
        # NOTE: This is the best stage to submit our tasks to the indexer
        #       since zope.sqlalchemy will flush in tpc_begin and start
        #       commiting things in tpc_vote, but our tpc_vote will run
        #       before theirs.
        if self.session is None:
            return

        assert self.indexer is not None
        assert self.queue is not None
        self.indexer.process(self.queue, self.session)

    def tpc_abort(self, transaction: ITransaction) -> None:
        if self.session is not None:
            self._finish()

    def tpc_finish(self, transaction: ITransaction) -> None:
        if self.session is not None:
            self._finish()

    def savepoint(self) -> IndexerSavepoint:
        assert self.queue is not None
        assert self.session is not None
        # this ensures everything up to the savepoint has been recorded
        self.session.flush()
        return IndexerSavepoint(self.queue)


class IndexerSavepoint:
    def __init__(self, queue: TaskQueue) -> None:
        self.queue = queue
        self.saved_size = len(queue)

    def rollback(self) -> None:
        del self.queue[self.saved_size:]
