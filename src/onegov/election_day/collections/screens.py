from __future__ import annotations

from onegov.core.collection import Pagination
from onegov.election_day.models import Screen


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class ScreenCollection(Pagination[Screen]):

    page: int

    def __init__(self, session: Session, page: int = 0):
        super().__init__(page)
        self.session = session

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page

    def subset(self) -> Query[Screen]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, index)

    def query(self) -> Query[Screen]:
        return self.session.query(Screen).order_by(Screen.number)

    def by_id(self, id: int) -> Screen | None:
        return self.query().filter(Screen.id == id).first()

    def by_number(self, number: int) -> Screen | None:
        return self.query().filter(Screen.number == number).first()

    def add(self, screen: Screen) -> None:
        self.session.add(screen)
        self.session.flush()

    def delete(self, screen: Screen) -> None:
        self.session.delete(screen)
        self.session.flush()

    def export(self) -> list[dict[str, Any]]:
        return [
            {
                'number': screen.number,
                'description': screen.description,
                'type': screen.type,
                'structure': screen.structure,
                'css': screen.css,
                'group': screen.group,
                'duration': screen.duration,
            }
            for screen in self.query()
        ]
