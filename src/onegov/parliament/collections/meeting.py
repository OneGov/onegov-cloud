from __future__ import annotations


import sedate

from onegov.core.collection import GenericCollection, Pagination

from typing import TYPE_CHECKING, Self

from onegov.parliament.models import Meeting

if TYPE_CHECKING:
    from uuid import UUID
    from sqlalchemy.orm import Query, Session


class MeetingCollection(
    GenericCollection[Meeting],
    Pagination[Meeting]
):

    def __init__(
        self,
        session: Session,
        page: int = 0,
        # tags: Sequence[str] | None = None,
        # filter_keywords: Mapping[str, list[str] | str] | None = None,
    ) -> None:
        super().__init__(session, page=page)
        self.page = page
        # self.tags = tags if tags else [],
        # self.filter_keywords = filter_keywords or {}

    @property
    def model_class(self) -> type[Meeting]:
        return Meeting

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
        )

    def query(self) -> Query[Meeting]:
        return super().query()

    def query_future_meetings(self) -> Query[Meeting]:
        return (
            self.query()
            .filter(Meeting.start_datetime >= sedate.utcnow())
            .order_by(Meeting.start_datetime.asc())
        )

    def query_past_meetings(self) -> Query[Meeting]:
        return (
            self.query()
            .filter(Meeting.start_datetime < sedate.utcnow())
            .order_by(Meeting.start_datetime.desc())
        )

    def by_id(self, id: UUID | int | str) -> Meeting | None:
        return self.query().filter(Meeting.id == id).first()

    def subset(self) -> Query[Meeting]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index)

    @property
    def page_index(self) -> int:
        return self.page

    # def for_filter(
    #     self,
    #     *,
    #     tags: Sequence[str] | None = None,
    #     tag: str | None = None
    # ) -> Self:
    #     """ Returns a new collection with the given tags applied. """
    #
    #     tags = list(self.tags if tags is None else tags)
    #     if tag is not None:
    #         if tag in tags:
    #             tags.remove(tag)
    #         else:
    #             tags.append(tag)
    #
    #     return self.__class__(self.session, page=self.page, tags=tags)
