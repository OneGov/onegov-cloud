from onegov.core.collection import GenericCollection, Pagination
from onegov.core.utils import toggle
from onegov.directory.models import DirectoryEntry
from sqlalchemy.orm import object_session
from sqlalchemy.dialects.postgresql import array


class DirectoryEntryCollection(GenericCollection, Pagination):

    def __init__(self, directory, type='*', extra_parameters=None, page=0):
        super().__init__(object_session(directory))
        self.type = type
        self.directory = directory
        self.extra_parameters = extra_parameters or {}
        self.page = page

    def __eq__(self, other):
        return self.type == other.type and self.page == other.page

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.directory,
            self.type,
            self.extra_parameters,
            page=index
        )

    def by_name(self, name):
        return self.query().filter_by(name=name).first()

    def query(self):
        query = super().query().filter_by(directory_id=self.directory.id)
        keywords = self.valid_keywords(self.extra_parameters)

        values = {
            ':'.join((keyword, value))
            for keyword in keywords
            for value in keywords[keyword]
        }

        if values:
            query = query.filter(
                self.model_class._keywords.has_all(array(values)))

        return query

    def valid_keywords(self, parameters):
        return {
            k: v for k, v in parameters.items()
            if k in set(self.directory.configuration.keywords)
        }

    @property
    def name(self):
        return self.directory.name

    @property
    def model_class(self):
        return DirectoryEntry.get_polymorphic_class(self.type, DirectoryEntry)

    def for_filter(self, **keywords):
        if not self.directory.configuration.keywords:
            return self

        parameters = self.extra_parameters.copy()

        for keyword, value in self.valid_keywords(keywords).items():
            collection = set(parameters.get(keyword, []))
            collection = toggle(collection, value)

            if collection:
                parameters[keyword] = tuple(collection)
            elif keyword in parameters:
                del parameters[keyword]

        return self.__class__(self.directory, self.type, parameters)
