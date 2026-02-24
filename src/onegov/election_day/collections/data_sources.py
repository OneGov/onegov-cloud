from __future__ import annotations

from sqlalchemy import desc

from onegov.core.collection import Pagination
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self
    from uuid import UUID


class DataSourceCollection(Pagination[DataSource]):

    page: int

    def __init__(self, session: Session, page: int = 0):
        super().__init__(page)
        self.session = session

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page

    def subset(self) -> Query[DataSource]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, index)

    def query(self) -> Query[DataSource]:
        return self.session.query(DataSource).order_by(
            desc(DataSource.created))

    def by_id(self, id: UUID) -> DataSource | None:
        return self.query().filter(DataSource.id == id).first()

    def add(self, source: DataSource) -> None:
        self.session.add(source)
        self.session.flush()

    def delete(self, source: DataSource) -> None:
        self.session.delete(source)
        self.session.flush()


class DataSourceItemCollection(Pagination[DataSourceItem]):

    page: int

    def __init__(
        self,
        session: Session,
        id: UUID | None = None,
        page: int = 0
    ):
        super().__init__(page)
        self.session = session
        self.id = id

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page

    def subset(self) -> Query[DataSourceItem]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, self.id, index)

    def query(self) -> Query[DataSourceItem]:
        query = self.session.query(DataSourceItem)
        query = query.filter(DataSourceItem.source_id == self.id)
        query = query.order_by(DataSourceItem.district, DataSourceItem.number)
        return query

    def by_id(self, id: UUID) -> DataSourceItem | None:
        query = self.session.query(DataSourceItem)
        query = query.filter(DataSourceItem.id == id)
        return query.first()

    @property
    def source(self) -> DataSource | None:
        query = self.session.query(DataSource)
        query = query.filter(DataSource.id == self.id)
        return query.first()

    def add(self, item: DataSourceItem) -> None:
        assert self.id is not None
        item.source_id = self.id
        self.session.add(item)
        self.session.flush()

    def delete(self, item: DataSourceItem) -> None:
        self.session.delete(item)
        self.session.flush()
