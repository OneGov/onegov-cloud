from collections.abc import Callable, Iterable
from typing import Protocol

from transaction._manager import Attempt, ThreadTransactionManager, TransactionManager as TransactionManager
from transaction._transaction import Savepoint as Savepoint, Transaction as Transaction

class _CreateSavepoint(Protocol):
    def __call__(self, optimistic: bool = False) -> Savepoint: ...

class _CreateAttempts(Protocol):
    def __call__(self, number: int = 3) -> Iterable[Attempt]: ...

manager: ThreadTransactionManager
get: Callable[[], Transaction]
__enter__: Callable[[], Transaction]
begin: Callable[[], Transaction]
commit: Callable[[], None]
abort: Callable[[], None]
__exit__: Callable[[object, object, object], None]
doom: Callable[[], None]
isDoomed: Callable[[], bool]
savepoint: _CreateSavepoint
attempts: _CreateAttempts
