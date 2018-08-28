from onegov.core.collection import GenericCollection
from onegov.swissvotes.models import TranslatablePage


class TranslatablePageCollection(GenericCollection):

    @property
    def model_class(self):
        return TranslatablePage
