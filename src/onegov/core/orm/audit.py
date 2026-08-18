from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from onegov.core.collection import Pagination
from onegov.core.orm import Base
from onegov.core.orm.session_manager import CURRENT_USER_ID, CURRENT_USERNAME
from sedate import utcnow
from sqlalchemy import desc, Enum, event, Index, insert
from sqlalchemy.orm import mapped_column, Mapped, Session


from typing import Any, Literal, NamedTuple, Self, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from sqlalchemy.orm import Query


type AuditOperation = Literal['insert', 'update', 'delete']
type SnapshotFactory = Callable[[Any], dict[str, Any]]
type PreviousSnapshot = Callable[[Session, Any], dict[str, Any]]
type Changed = Callable[[Session, Any], bool]
type DeleteSnapshot = Callable[[Session, Any], dict[str, Any] | None]


STAGED_AUDIT_ENTRIES: str = 'staged_audit_entries'


class AuditModelConfig(NamedTuple):
    snapshot: SnapshotFactory
    previous_snapshot: PreviousSnapshot
    changed: Changed
    delete_snapshot: DeleteSnapshot | None


AUDIT_MODELS: dict[type[Any], AuditModelConfig] = {}


class StagedAuditEntry(NamedTuple):
    operation: AuditOperation
    instance: Any
    snapshot: dict[str, Any] | None
    previous_snapshot: dict[str, Any]
    config: AuditModelConfig
    user_id: str | None
    username: str
    created: datetime


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


@event.listens_for(Session, 'before_flush')
def prepare_audit_entries(
    session: Session,
    flush_context: Any,
    instances: Any,
) -> None:
    session.info.pop(STAGED_AUDIT_ENTRIES, None)
    if CURRENT_USERNAME not in session.info:
        return

    user_id = session.info.get(CURRENT_USER_ID)
    username = session.info[CURRENT_USERNAME]
    created = utcnow()

    staged: list[StagedAuditEntry] = [
        StagedAuditEntry(
            'insert',
            instance,
            None,
            {},
            config,
            user_id,
            username,
            created,
        )
        for instance in session.new
        if (config := audit_config(instance)) is not None
    ]

    staged.extend(
        StagedAuditEntry(
            'update',
            instance,
            None,
            config.previous_snapshot(session, instance),
            config,
            user_id,
            username,
            created,
        )
        for instance in session.dirty
        if (
            (config := audit_config(instance)) is not None
            and instance not in session.deleted
            and config.changed(session, instance)
        )
    )

    staged.extend(
        StagedAuditEntry(
            'delete',
            instance,
            snapshot,
            {},
            config,
            user_id,
            username,
            created,
        )
        for instance in session.deleted
        if (config := audit_config(instance)) is not None
        if (
            snapshot := (
                config.delete_snapshot(session, instance)
                if config.delete_snapshot is not None
                else config.snapshot(instance)
            )
        )
        is not None
    )

    if staged:
        session.info[STAGED_AUDIT_ENTRIES] = staged


@event.listens_for(Session, 'after_flush_postexec')
def write_audit_entries(session: Session, flush_context: Any) -> None:
    staged = session.info.pop(STAGED_AUDIT_ENTRIES, ())
    if not staged:
        return

    # Audited models are expected to have a single ``id`` primary key.
    values: list[dict[str, Any]] = [
        {
            'target_table': entry.instance.__tablename__,
            'target_id': str(entry.instance.id),
            'operation': entry.operation,
            'snapshot': (
                entry.snapshot
                if entry.snapshot is not None
                else entry.config.snapshot(entry.instance)
            ),
            'previous_snapshot': entry.previous_snapshot,
            'user_id': entry.user_id,
            'username': entry.username,
            'created': entry.created,
        }
        for entry in staged
    ]

    session.connection().execute(insert(AuditEntry), values)


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
