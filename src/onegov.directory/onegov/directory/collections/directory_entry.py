from onegov.core.collection import GenericCollection, Pagination
from onegov.core.utils import toggle
from onegov.directory.models import DirectoryEntry
from onegov.form import as_internal_id
from sqlalchemy.orm import object_session
from sqlalchemy.dialects.postgresql import array


class DirectoryEntryCollection(GenericCollection, Pagination):
    """ Provides a view on a directory's entries.

    The directory itself might be a natural place for lots of these methods
    to reside, but ultimately we want to avoid mixing the concerns of the
    directory model and this view-supporting collection.

    """

    def __init__(self, directory, type='*', keywords=None, page=0):
        super().__init__(object_session(directory))

        self.type = type
        self.directory = directory
        self.keywords = keywords or {}
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
            self.keywords,
            page=index
        )

    def by_name(self, name):
        return self.query().filter_by(name=name).first()

    def query(self):
        query = super().query().filter_by(directory_id=self.directory.id)
        keywords = self.valid_keywords(self.keywords)

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
            as_internal_id(k): v for k, v in parameters.items()
            if k in {
                as_internal_id(kw)
                for kw in self.directory.configuration.keywords
            }
        }

    @property
    def directory_name(self):
        return self.directory.name

    @property
    def model_class(self):
        return DirectoryEntry.get_polymorphic_class(self.type, DirectoryEntry)

    @property
    def available_filters(self):
        keywords = tuple(
            as_internal_id(k)
            for k in self.directory.configuration.keywords or tuple()
        )
        fields = {f.id: f for f in self.directory.fields if f.id in keywords}

        return (
            (k, fields[k].label, sorted([c.label for c in fields[k].choices]))
            for k in keywords
        )

    def for_filter(self, singular=False, **keywords):
        if not self.directory.configuration.keywords:
            return self

        parameters = self.keywords.copy()

        for keyword, value in self.valid_keywords(keywords).items():
            collection = set(parameters.get(keyword, []))

            if singular:
                collection = set() if value in collection else {value}
            else:
                collection = toggle(collection, value)

            if collection:
                parameters[keyword] = list(collection)
            elif keyword in parameters:
                del parameters[keyword]

        return self.__class__(self.directory, self.type, parameters)
