from collections.abc import Callable, Iterable, Sequence
from typing import Any, Protocol, TypeVar, overload
from typing_extensions import TypeVarTuple, Unpack

# NOTE: We use Protocol instead of Interface for better type checker support

_T = TypeVar("_T")
_Ts = TypeVarTuple("_Ts")

class _Attempt(Protocol):
    def __enter__(self) -> ITransaction: ...
    def __exit__(self, t: object, v: object, tb: object, /) -> bool | None: ...


class ITransactionManager(Protocol):
    @property
    def explicit(self) -> bool: ...
    def begin(self) -> ITransaction: ...
    def get(self) -> ITransaction: ...
    def commit(self) -> object: ...
    def abort(self) -> object: ...
    def doom(self) -> object: ...
    def isDoomed(self) -> bool: ...
    def savepoint(self, optimistic: bool = False, /) -> ISavepoint: ...
    def registerSynch(self, synch: ISynchronizer, /) -> object: ...
    def unregisterSynch(self, synch: ISynchronizer, /) -> object: ...
    def clearSynchs(self) -> object: ...
    def registeredSynchs(self) -> bool: ...
    def attempts(self, number: int = 3, /) -> Iterable[_Attempt]: ...
    @overload
    def run(self, func: Callable[[], _T], tries: int = 3, /) -> _T: ...
    @overload
    def run(self, func: None = None, tries: int = 3, /) -> Callable[[Callable[[], _T]], _T]: ...
    @overload
    def run(self, tries: int, /) -> Callable[[Callable[[], _T]], _T]: ...

class ITransaction(Protocol):
    @property
    def user(self) -> str: ...
    @property
    def description(self) -> str: ...
    @property
    def extension(self) -> dict[str, Any]: ...
    def commit(self) -> object: ...
    def abort(self) -> object: ...
    def doom(self) -> object: ...
    def savepoint(self, optimistic: bool = False, /) -> ISavepoint: ...
    def join(self, datamanager: IDataManager, /) -> object: ...
    def note(self, text: str, /) -> object: ...
    def setExtendedInfo(self, name: str, value: object, /) -> object: ...
    @overload
    def addBeforeCommitHook(self, hook: Callable[[], object], args: tuple[()] = (), kws: None = None, /) -> object: ...
    @overload
    def addBeforeCommitHook(self, hook: Callable[[Unpack[_Ts]], object], args: tuple[Unpack[_Ts]], kws: None = None, /) -> object: ...  # noqa: Y090
    @overload
    def addBeforeCommitHook(self, hook: Callable[..., object], args: Sequence[Any], kws: dict[str, Any], /) -> object: ...
    def getBeforeCommitHooks(self) -> Iterable[tuple[Callable[..., object], Sequence[Any], dict[str, Any]]]: ...
    @overload
    def addAfterCommitHook(self, hook: Callable[[bool], object], args: tuple[()] = (), kws: None = None, /) -> object: ...
    @overload
    def addAfterCommitHook(self, hook: Callable[[bool, Unpack[_Ts]], object], args: tuple[Unpack[_Ts]], kws: None = None, /) -> object: ...  # noqa: Y090
    @overload
    def addAfterCommitHook(self, hook: Callable[[bool, Unpack[tuple[Any, ...]]], object], args: Sequence[Any], kws: dict[str, Any], /) -> object: ...
    def getAfterCommitHooks(self) -> Iterable[tuple[Callable[[bool, Unpack[tuple[Any, ...]]], object], Sequence[Any], dict[str, Any]]]: ...
    @overload
    def addBeforeAbortHook(self, hook: Callable[[], object], args: tuple[()] = (), kws: None = None, /) -> object: ...
    @overload
    def addBeforeAbortHook(self, hook: Callable[[Unpack[_Ts]], object], args: tuple[Unpack[_Ts]], kws: None = None, /) -> object: ...  # noqa: Y090
    @overload
    def addBeforeAbortHook(self, hook: Callable[..., object], args: Sequence[Any], kws: dict[str, Any], /) -> object: ...
    def getBeforeAbortHooks(self) -> Iterable[tuple[Callable[..., object], Sequence[Any], dict[str, Any]]]: ...
    @overload
    def addAfterAbortHook(self, hook: Callable[[], object], args: tuple[()] = (), kws: None = None, /) -> object: ...
    @overload
    def addAfterAbortHook(self, hook: Callable[[Unpack[_Ts]], object], args: tuple[Unpack[_Ts]], kws: None = None, /) -> object: ...  # noqa: Y090
    @overload
    def addAfterAbortHook(self, hook: Callable[..., object], args: Sequence[Any], kws: dict[str, Any], /) -> object: ...
    def getAfterAbortHooks(self) -> Iterable[tuple[Callable[..., object], Sequence[Any], dict[str, Any]]]: ...
    def set_data(self, ob: object, data: object, /) -> object: ...
    def data(self, ob: object, /) -> Any: ...
    def isRetryableError(self, error: BaseException, /) -> bool: ...

class IDataManager(Protocol):
    @property
    def transaction_manager(self) -> ITransactionManager: ...
    def abort(self, transaction: ITransaction, /) -> object: ...
    def tpc_begin(self, transaction: ITransaction, /) -> object: ...
    def commit(self, transaction: ITransaction, /) -> object: ...
    def tpc_vote(self, transaction: ITransaction, /) -> object: ...
    def tpc_finish(self, transaction: ITransaction, /) -> object: ...
    def tpc_abort(self, transaction: ITransaction, /) -> object: ...
    def sortKey(self) -> str: ...

class ISynchronizer(Protocol):
    def beforeCompletion(self, transaction: ITransaction, /) -> object: ...
    def afterCompletion(self, transaction: ITransaction, /) -> object: ...
    def newTransaction(self, transaction: ITransaction, /) -> object: ...

class ISavepointDataManager(IDataManager, Protocol):
    def savepoint(self) -> IDataManagerSavepoint: ...

class IRetryDataManager(IDataManager, Protocol):
    def should_retry(self, exception: BaseException, /) -> bool: ...

class IDataManagerSavepoint(Protocol):
    def rollback(self) -> object: ...

class ISavepoint(Protocol):
    def rollback(self) -> object: ...
    @property
    def valid(self) -> bool: ...

class InvalidSavepointRollbackError(Exception): ...

class TransactionError(Exception): ...
class TransactionFailedError(TransactionError): ...
class DoomedTransaction(TransactionError): ...
class TransientError(TransactionError): ...
class NoTransaction(TransactionError): ...
class AlreadyInTransaction(TransactionError): ...
