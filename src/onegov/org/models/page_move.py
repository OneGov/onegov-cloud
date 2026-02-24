from __future__ import annotations

from onegov.page import Page, PageCollection


from typing import Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm.abstract import (
        AdjacencyList, AdjacencyListCollection, MoveDirection)
    from sqlalchemy.orm import Session


_L = TypeVar('_L', bound='AdjacencyList')


class AdjacencyListMove(Generic[_L]):
    """ Represents a single move of an adjacency list item. """

    __collection__: type[AdjacencyListCollection[_L]]

    def __init__(
        self,
        session: Session,
        subject: _L,
        target: _L,
        direction: MoveDirection
    ) -> None:
        self.session = session
        self.subject = subject
        self.target = target
        self.direction = direction

    @property
    def subject_id(self) -> int:
        return self.subject.id

    @property
    def target_id(self) -> int:
        return self.target.id

    def execute(self) -> None:
        self.__collection__(self.session).move(
            subject=self.subject,
            target=self.target,
            direction=self.direction
        )


class PageMove(AdjacencyListMove[Page]):
    __collection__ = PageCollection
