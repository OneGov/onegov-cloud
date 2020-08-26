from onegov.core.collection import GenericCollection
from onegov.translator_directory.models.translator import Language


class LanguageCollection(GenericCollection):

    @property
    def model_class(self):
        return Language

    def query(self):
        return super().query().order_by(Language.name)
