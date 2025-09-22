from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.pas.models.import_log import ImportLog
from onegov.user import User
from sqlalchemy.orm import load_only, joinedload

from typing import Self, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from sqlalchemy.orm import Query


class ImportLogCollection(GenericCollection[ImportLog]):
    """Collection for managing import logs."""

    def __init__(
        self,
        session: Session,
        status: str | None = None
    ):
        super().__init__(session)
        self.status = status

    @property
    def model_class(self) -> type[ImportLog]:
        return ImportLog

    def query(self) -> Query[ImportLog]:
        query = super().query()

        if self.status is not None:
            query = query.filter(ImportLog.status == self.status)

        return query.order_by(ImportLog.created.desc())

    def for_filter(
        self,
        status: str | None = None
    ) -> Self:
        return self.__class__(self.session, status)

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
