from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models.import_log import ImportLog


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
