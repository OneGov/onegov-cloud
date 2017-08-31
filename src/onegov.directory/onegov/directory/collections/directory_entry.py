from onegov.core.collection import GenericCollection
from onegov.directory.models import DirectoryEntry
from onegov.core.utils import toggle


class DirectoryEntryCollection(GenericCollection):

    def __init__(self, session, directory, type='*', extra_parameters=None):
        super().__init__(session)
        self.type = type
        self.directory = directory
        self.extra_parameters = extra_parameters or {}

    @property
    def directory_name(self):
        return self.directory.name

    @property
    def model_class(self):
        return DirectoryEntry.get_polymorphic_class(self.type, DirectoryEntry)

    def for_filter(self, **keywords):
        if not self.directory.configuration.keywords:
            return self

        available = set(self.directory.configuration.keywords)
        keywords = {k: v for k, v in keywords.items() if k in available}
        parameters = self.extra_parameters.copy()

        for keyword, value in keywords.items():
            collection = set(parameters.get(keyword, []))
            collection = toggle(collection, value)

            if collection:
                parameters[keyword] = tuple(collection)
            elif keyword in parameters:
                del parameters[keyword]

        return self.__class__(
            self.session, self.directory, self.type, parameters)
