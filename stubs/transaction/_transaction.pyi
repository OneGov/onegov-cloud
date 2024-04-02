from collections.abc import Callable, Iterator, Sequence
from logging import Logger
from typing import Any, overload
from typing_extensions import TypeVarTuple, Unpack

from transaction.interfaces import IDataManager, ISynchronizer, ITransactionManager
from transaction.weakset import WeakSet

_Ts = TypeVarTuple("_Ts")

class Status:
    ACTIVE: str
    COMMITTING: str
    COMMITTED: str
    DOOMED: str
    COMMITFAILED: str

class _NoSynchronizers:
    @staticmethod
    def map(_f: Callable[..., object]) -> None: ...

class Transaction:
    status: str
    extension: dict[str, Any]
    log: Logger
    def __init__(self, synchronizers: WeakSet[ISynchronizer] | None = None, manager: ITransactionManager | None = None) -> None: ...
    @property
    def user(self) -> str: ...
    @user.setter
    def user(self, v: str) -> None: ...
    @property
    def description(self) -> str: ...
    @description.setter
    def description(self, v: str) -> None: ...
    def isDoomed(self) -> bool: ...
    def doom(self) -> None: ...
    def join(self, resource: IDataManager) -> None: ...
    def savepoint(self, optimistic: bool = False) -> Savepoint: ...
    def commit(self) -> None: ...
    def getBeforeCommitHooks(self) -> Iterator[tuple[Callable[..., object], Sequence[Any], dict[str, Any]]]: ...
    @overload
    def addBeforeCommitHook(self, hook: Callable[[], object], args: tuple[()] = (), kws: None = None) -> object: ...
    @overload
    def addBeforeCommitHook(self, hook: Callable[[Unpack[_Ts]], object], args: tuple[Unpack[_Ts]], kws: None = None) -> object: ...  # noqa: Y090
    @overload
    def addBeforeCommitHook(self, hook: Callable[..., object], args: Sequence[Any], kws: dict[str, Any]) -> object: ...
    def getAfterCommitHooks(self) -> Iterator[tuple[Callable[[bool, Unpack[tuple[Any, ...]]], object], Sequence[Any], dict[str, Any]]]: ...
    @overload
    def addAfterCommitHook(self, hook: Callable[[bool], object], args: tuple[()] = (), kws: None = None) -> object: ...
    @overload
    def addAfterCommitHook(self, hook: Callable[[bool, Unpack[_Ts]], object], args: tuple[Unpack[_Ts]], kws: None = None) -> object: ...  # noqa: Y090
    @overload
    def addAfterCommitHook(self, hook: Callable[[bool, Unpack[tuple[Any, ...]]], object], args: Sequence[Any], kws: dict[str, Any]) -> object: ...
    def getBeforeAbortHooks(self) -> Iterator[tuple[Callable[..., object], Sequence[Any], dict[str, Any]]]: ...
    @overload
    def addBeforeAbortHook(self, hook: Callable[[], object], args: tuple[()] = (), kws: None = None) -> object: ...
    @overload
    def addBeforeAbortHook(self, hook: Callable[[Unpack[_Ts]], object], args: tuple[Unpack[_Ts]], kws: None = None) -> object: ...  # noqa: Y090
    @overload
    def addBeforeAbortHook(self, hook: Callable[..., object], args: Sequence[Any], kws: dict[str, Any]) -> object: ...
    def getAfterAbortHooks(self) -> Iterator[tuple[Callable[..., object], Sequence[Any], dict[str, Any]]]: ...
    @overload
    def addAfterAbortHook(self, hook: Callable[[], object], args: tuple[()] = (), kws: None = None) -> object: ...
    @overload
    def addAfterAbortHook(self, hook: Callable[[Unpack[_Ts]], object], args: tuple[Unpack[_Ts]], kws: None = None) -> object: ...  # noqa: Y090
    @overload
    def addAfterAbortHook(self, hook: Callable[..., object], args: Sequence[Any], kws: dict[str, Any]) -> object: ...
    def data(self, ob: object) -> Any: ...
    def set_data(self, ob: object, ob_data: object) -> None: ...
    def abort(self) -> None: ...
    def note(self, text: str | None) -> None: ...
    def setUser(self, user_name: str, path: str = "/") -> None: ...
    def setExtendedInfo(self, name: str, value: object) -> None: ...
    def isRetryableError(self, error: BaseException) -> bool: ...

def rm_key(rm: object) -> str | None: ...

class Savepoint:
    transaction: Transaction
    def __init__(self, transaction: Transaction, optimistic: bool, *resources: IDataManager) -> None: ...
    @property
    def valid(self) -> bool: ...
    def rollback(self) -> None: ...

class AbortSavepoint:
    datamanager: IDataManager
    transaction: Transaction
    def __init__(self, datamanager: IDataManager, transaction: Transaction) -> None: ...
    def rollback(self) -> None: ...

class NoRollbackSavepoint:
    datamanager: IDataManager
    def __init__(self, datamanager: IDataManager) -> None: ...
    def rollback(self) -> None: ...

def text_or_warn(s: object) -> str: ...
