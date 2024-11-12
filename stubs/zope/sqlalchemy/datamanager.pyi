from collections.abc import Callable
from typing import Any, Final, Literal
from typing_extensions import TypeAlias

from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from transaction.interfaces import ITransaction, ITransactionManager

_Status: TypeAlias = Literal["active", "changed", "readonly"]
# TODO: Replace these with the proper types after SQLAlchemy 2.0 upgrade
_ORMExecuteState: TypeAlias = Any
_SessionTransaction: TypeAlias = Any
_UOWTransaction: TypeAlias = Any

STATUS_ACTIVE: Final = "active"
STATUS_CHANGED: Final = "changed"
STATUS_READONLY: Final = "readonly"
STATUS_INVALIDATED: Final = STATUS_CHANGED
NO_SAVEPOINT_SUPPORT: Final[set[str]]
SA_GE_14: Final[bool]

class SessionDataManager:
    transaction_manager: ITransactionManager
    tx: ITransaction
    session: Session
    state: str
    keep_session: bool
    def __init__(self, session: Session, status: _Status, transaction_manager: ITransactionManager, keep_session: bool = False) -> None: ...
    def abort(self, trans: ITransaction) -> None: ...
    def tpc_begin(self, trans: ITransaction) -> None: ...
    def commit(self, trans: ITransaction) -> None: ...
    def tpc_vote(self, trans: ITransaction) -> None: ...
    def tpc_finish(self, trans: ITransaction) -> None: ...
    def tpc_abort(self, trans: ITransaction) -> None: ...
    def sortKey(self) -> str: ...
    @property
    def savepoint(self) -> Callable[[], SessionSavepoint]: ...
    def should_retry(self, error: BaseException) -> bool: ...

class TwoPhaseSessionDataManager(SessionDataManager): ...

class SessionSavepoint:
    session: Session
    transaction: _SessionTransaction
    def __init__(self, session: Session) -> None: ...
    def rollback(self) -> None: ...

def join_transaction(session: Session, initial_state: _Status = "active", transaction_manager: ITransactionManager = ..., keep_session: bool = False) -> None: ...
def mark_changed(session: Session, transaction_manager: ITransactionManager = ..., keep_session: bool = False) -> None: ...

class ZopeTransactionEvents:
    initial_state: _Status
    transaction_manager: ITransactionManager
    keep_session: bool
    def __init__(self, initial_state: _Status = "active", transaction_manager: ITransactionManager = ..., keep_session: bool = False) -> None: ...
    def after_begin(self, session: Session, transaction: _SessionTransaction, connection: Connection) -> None: ...
    def after_attach(self, session: Session, instance: object) -> None: ...
    def after_flush(self, session: Session, flush_context: _UOWTransaction) -> None: ...
    def after_bulk_update(self, update_context: object) -> None: ...
    def after_bulk_delete(self, delete_context: object) -> None: ...
    def before_commit(self, session: Session) -> None: ...
    def do_orm_execute(self, execute_state: _ORMExecuteState) -> None: ...
    def mark_changed(self, session: Session) -> None: ...
    def join_transaction(self, session: Session) -> None: ...

def register(session: Session | Callable[[], Session], initial_state: _Status = "active", transaction_manager: ITransactionManager = ..., keep_session: bool = False) -> ZopeTransactionEvents: ...
