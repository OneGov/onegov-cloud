from cached_property import cached_property
from sqlalchemy import func

from onegov.core.collection import GenericCollection, Pagination
from onegov.translator_directory.models.translator import Language


class LanguageCollection(GenericCollection, Pagination):

    batch_size = 20

    def __init__(
            self, session,
            page=0,
            letter=None
    ):
        super().__init__(session)
        self.page = page
        self.letter = letter.upper() if letter else None

    @property
    def model_class(self):
        return Language

    def query(self):
        query = super().query()
        if self.letter:
            query = query.filter(
                func.unaccent(Language.name).startswith(self.letter))
        return query.order_by(Language.name)

    def __eq__(self, other):
        return other.page == self.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, page=index)

    @cached_property
    def used_letters(self):
        """ Returns a list of all the distinct first letters of the peoples
        last names.

        """
        letter = func.left(Language.name, 1)
        letter = func.unaccent(letter)
        query = self.session.query(letter.distinct().label('letter'))
        query = query.order_by(letter)
        return [r.letter for r in query if r.letter]

    def by_letter(self, letter):
        return self.__class__(
            session=self.session,
            page=0,
            letter=letter
        )
