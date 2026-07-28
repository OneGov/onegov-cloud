from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.pas.models.import_log import ImportLog
from onegov.user import User
from sqlalchemy.orm import load_only, joinedload

from typing import Self, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from sqlalchemy.orm import Query
    from uuid import UUID


class ImportLogCollection(GenericCollection[ImportLog, 'UUID']):
    """Collection for managing import logs."""

    def __init__(
        self,
        session: Session,
        status: str | None = None,
        user_id: UUID | None = None,
    ):
        super().__init__(session)
        self.status = status
        self.user_id = user_id

    @property
    def model_class(self) -> type[ImportLog]:
        return ImportLog

    def query(self) -> Query[ImportLog]:
        query = super().query()

        if self.status is not None:
            query = query.filter(ImportLog.status == self.status)

        if self.user_id is not None:
            query = query.filter(ImportLog.user_id == self.user_id)

        return query.order_by(ImportLog.created.desc())

    def for_filter(
        self, status: str | None = None, user_id: UUID | None = None
    ) -> Self:
        return self.__class__(self.session, status, user_id)

    def distinct_users(self) -> list[User]:
        return (
            self.session.query(User)
            .filter(
                User.id.in_(
                    self.session.query(ImportLog.user_id)
                    .filter(ImportLog.user_id.isnot(None))
                    .distinct()
                )
            )
            .order_by(User.username)
            .all()
        )

    def for_listing(self, limit: int = 50) -> Query[ImportLog]:
        """Optimized query for listing import logs with minimal data."""
        return (
            self.query()
            .options(
                load_only(
                    ImportLog.id,
                    ImportLog.created,
                    ImportLog.import_type,
                    ImportLog.status,
                    ImportLog.user_id
                ),
                joinedload(ImportLog.user).load_only(User.username)
            )
            .limit(limit)
        )

    def most_recent_completed_cli_import(self) -> ImportLog | None:
        """Get the most recent completed CLI import log."""
        return self.session.query(ImportLog).filter_by(
            import_type='cli',
            status='completed'
        ).order_by(ImportLog.created.desc()).first()
