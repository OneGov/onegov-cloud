from onegov.core.collection import GenericCollection, Pagination
from onegov.translator_directory.models.translator import Language


class LanguageCollection(GenericCollection, Pagination):

    batch_size = 20

    def __init__(
            self, session,
            page=0,
    ):
        super().__init__(session)
        self.page = page

    @property
    def model_class(self):
        return Language

    def query(self):
        return super().query().order_by(Language.name)

    def by_ids(self, ids):
        return self.session.query(Language).filter(
            Language.id.in_(ids)
        )

    def __eq__(self, other):
        return other.page == self.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, page=index)
