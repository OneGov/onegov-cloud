from onegov.core.collection import GenericCollection
from onegov.translator_directory.models.translator import Language


class LanguageCollection(GenericCollection):

    @property
    def model_class(self):
        return Language
