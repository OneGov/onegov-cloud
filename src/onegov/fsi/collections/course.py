from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.fsi.models.course import Course


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.models import CourseAttendee
    from sqlalchemy.orm import Query, Session
    from typing import Self
    from uuid import UUID


class CourseCollection(GenericCollection[Course]):
    def __init__(
        self,
        session: Session,
        # TODO: Why do we have this argument? We don't use it
        auth_attendee: CourseAttendee | None = None,
        show_hidden_from_public: bool = False,
    ) -> None:
        super().__init__(session)
        self.auth_attendee = auth_attendee
        self.show_hidden_from_public = show_hidden_from_public

    @property
    def model_class(self) -> type[Course]:
        return Course

    def query(self) -> Query[Course]:
        query = super().query()
        if not self.show_hidden_from_public:
            query = query.filter_by(hidden_from_public=False)
        return query.order_by(Course.name)

    def by_id(
        self,
        id: UUID  # type:ignore[override]
    ) -> Course | None:
        return super().query().filter(self.primary_key == id).first()

    def toggled_hidden(self) -> Self:
        return self.__class__(
            self.session,
            self.auth_attendee,
            show_hidden_from_public=not self.show_hidden_from_public
        )
