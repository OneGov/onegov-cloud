from __future__ import annotations

from functools import cached_property
from sqlalchemy import func

from onegov.core.collection import GenericCollection, Pagination
from onegov.translator_directory.models.language import Language


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from typing import Self


class LanguageCollection(GenericCollection[Language], Pagination[Language]):

    batch_size = 20

    def __init__(
        self,
        session: Session,
        page: int = 0,
        letter: str | None = None
    ) -> None:
        super().__init__(session)
        self.page = page
        self.letter = letter.upper() if letter else None

    @property
    def model_class(self) -> type[Language]:
        return Language

    def query(self) -> Query[Language]:
        query = super().query()
        if self.letter:
            query = query.filter(
                func.unaccent(Language.name).startswith(self.letter))
        return query.order_by(Language.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.page == self.page

    def subset(self) -> Query[Language]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index)

    @cached_property
    def used_letters(self) -> list[str]:
        """ Returns a list of all the distinct first letters of the peoples
        last names.

        """
        letter = func.left(Language.name, 1)
        letter = func.unaccent(letter)
        query = self.session.query(letter.distinct().label('letter'))
        query = query.order_by(letter)
        return [r.letter for r in query if r.letter]

    def by_letter(self, letter: str | None) -> Self:
        return self.__class__(
            session=self.session,
            page=0,
            letter=letter
        )
