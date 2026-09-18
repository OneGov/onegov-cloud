from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from onegov.core.collection import Pagination
from onegov.core.orm import Base, SessionManager
from sedate import utcnow
from sqlalchemy import desc, Enum, Index, insert, inspect, select
from sqlalchemy.orm import mapped_column, Mapped, object_session, Session


from typing import Any, Literal, NamedTuple, Self, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from sqlalchemy.orm import Query


type AuditOperation = Literal['insert', 'update', 'delete']
type SnapshotFactory = Callable[[Any], dict[str, Any]]
type PreviousSnapshot = Callable[[Session, Any], dict[str, Any] | None]
type Changed = Callable[[Session, Any], bool]
type DeleteSnapshot = Callable[[Session, Any], dict[str, Any] | None]


class AuditModelConfig(NamedTuple):
    snapshot: SnapshotFactory
    previous_snapshot: PreviousSnapshot
    changed: Changed
    delete_snapshot: DeleteSnapshot | None


AUDIT_MODELS: dict[type[Any], AuditModelConfig] = {}


def register_audit_model(
    model: type[Any],
    snapshot: SnapshotFactory,
    previous_snapshot: PreviousSnapshot,
    changed: Changed,
    delete_snapshot: DeleteSnapshot | None = None,
) -> None:
    AUDIT_MODELS[model] = AuditModelConfig(
        snapshot,
        previous_snapshot,
        changed,
        delete_snapshot,
    )


def audit_config(instance: Any) -> AuditModelConfig | None:
    return next(
        (
            AUDIT_MODELS[model]
            for model in type(instance).__mro__
            if model in AUDIT_MODELS
        ),
        None,
    )


class AuditEntry(Base):
    __tablename__ = 'audit_entries'

    #: The unique ID of this audit event
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    #: The table containing the affected record
    target_table: Mapped[str]

    #: The ID of the affected record
    target_id: Mapped[str]

    #: The database operation that caused the audit event
    operation: Mapped[AuditOperation] = mapped_column(
        Enum(
            'insert',
            'update',
            'delete',
            name='audit_operation',
        )
    )

    #: The state after insert/update or immediately before delete
    snapshot: Mapped[dict[str, Any]] = mapped_column(default=dict)

    #: The persisted state immediately before an update
    previous_snapshot: Mapped[dict[str, Any]] = mapped_column(default=dict)

    #: The immutable user ID responsible for the operation
    user_id: Mapped[str | None]

    #: The username responsible for the operation
    username: Mapped[str]

    #: The time at which the operation was captured
    created: Mapped[datetime] = mapped_column(default=utcnow)

    __table_args__ = (
        Index('audit_entries_target', 'target_table', 'target_id'),
        Index('audit_entries_created', 'created'),
    )


def latest_snapshot(
    session: Session,
    instance: Any,
) -> dict[str, Any] | None:
    return session.execute(
        select(AuditEntry.snapshot)
        .where(
            AuditEntry.target_table == instance.__tablename__,
            AuditEntry.target_id == str(instance.id),
        )
        .order_by(
            desc(AuditEntry.created),
            desc(AuditEntry.id),
        )
        .limit(1)
    ).scalar_one_or_none()


def column_snapshot(instance: Any) -> dict[str, Any]:
    state = inspect(instance)
    return {
        attribute.key: getattr(instance, attribute.key)
        for attribute in state.mapper.column_attrs
    }


def write_audit_entry(
    session: Session,
    instance: Any,
    operation: AuditOperation,
    snapshot: dict[str, Any],
    previous_snapshot: dict[str, Any] | None = None,
) -> None:
    session_manager = SessionManager.get_active()
    if session_manager is None:
        return

    username = session_manager.current_username
    if not isinstance(username, str):
        return

    session.connection().execute(
        insert(AuditEntry).values(
            target_table=instance.__tablename__,
            target_id=str(instance.id),
            operation=operation,
            snapshot=snapshot,
            previous_snapshot=previous_snapshot or {},
            user_id=session_manager.current_user_id,
            username=username,
            created=utcnow(),
        )
    )


def audit_insert(_schema: str, obj: object) -> None:
    config = audit_config(obj)
    session = object_session(obj)
    if config is None or session is None:
        return

    write_audit_entry(session, obj, 'insert', config.snapshot(obj))


def audit_update(_schema: str, obj: object) -> None:
    config = audit_config(obj)
    session = object_session(obj)
    if config is None or session is None:
        return
    if obj in session.dirty and not config.changed(session, obj):
        return

    previous_snapshot = latest_snapshot(session, obj)
    if previous_snapshot is None:
        previous_snapshot = config.previous_snapshot(session, obj)

    write_audit_entry(
        session,
        obj,
        'update',
        config.snapshot(obj),
        previous_snapshot,
    )


def audit_delete(
    _schema: str,
    session: Session,
    obj: object,
) -> None:
    config = audit_config(obj)
    if config is None:
        return

    state = inspect(obj)
    assert state is not None
    snapshot: dict[str, Any] | None
    if state.detached:
        snapshot = latest_snapshot(session, obj) or column_snapshot(obj)
    elif config.delete_snapshot is not None:
        snapshot = config.delete_snapshot(session, obj)
    else:
        snapshot = config.snapshot(obj)

    if snapshot is not None:
        write_audit_entry(session, obj, 'delete', snapshot)


def register_audit_handlers(session_manager: SessionManager) -> None:
    session_manager.on_insert.connect(audit_insert)
    session_manager.on_update.connect(audit_update)
    session_manager.on_delete.connect(audit_delete)


class AuditEntryCollection(Pagination[AuditEntry]):
    batch_size = 50

    def __init__(
        self,
        session: Session,
        page: int = 0,
        operation: AuditOperation | None = None,
    ) -> None:
        super().__init__(page)
        self.session = session
        self.operation = operation

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, AuditEntryCollection)
            and self.page == other.page
            and self.operation == other.operation
        )

    def query(self) -> Query[AuditEntry]:
        return self.session.query(AuditEntry)

    def subset(self) -> Query[AuditEntry]:
        query = self.query().order_by(
            desc(AuditEntry.created),
            desc(AuditEntry.id),
        )
        if self.operation is not None:
            query = query.filter(AuditEntry.operation == self.operation)
        return query

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, index, self.operation)

    def for_operation(self, operation: AuditOperation | None) -> Self:
        return self.__class__(self.session, operation=operation)

    def by_id(self, id: UUID) -> AuditEntry | None:
        return self.query().filter(AuditEntry.id == id).first()
