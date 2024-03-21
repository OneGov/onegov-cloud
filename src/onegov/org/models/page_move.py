from onegov.core.orm.abstract import MoveDirection
from onegov.core.utils import Bunch
from onegov.page import Page, PageCollection


from typing import Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm.abstract import AdjacencyList, AdjacencyListCollection
    from sqlalchemy.orm import Session
    from typing_extensions import Self


_L = TypeVar('_L', bound='AdjacencyList')


class AdjacencyListMove(Generic[_L]):
    """ Represents a single move of an adjacency list item. """

    __collection__: type['AdjacencyListCollection[_L]']

    def __init__(
        self,
        session: 'Session',
        subject: _L,
        target: _L,
        # FIXME: just use MoveDirection enum...
        direction: str
    ) -> None:
        self.session = session
        self.subject = subject
        self.target = target
        self.direction = direction

    # FIXME: This is a stupid hack... just use class_link to generate
    #        the url with the template subtitution strings
    @classmethod
    def for_url_template(cls) -> 'Self':
        return cls(
            session=None,  # type:ignore
            subject=Bunch(id='{subject_id}'),  # type:ignore
            target=Bunch(id='{target_id}'),  # type:ignore
            direction='{direction}'
        )

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
            direction=getattr(MoveDirection, self.direction)
        )


class PageMove(AdjacencyListMove[Page]):
    __collection__ = PageCollection
