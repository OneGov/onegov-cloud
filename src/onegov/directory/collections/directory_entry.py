from itertools import groupby
from onegov.core.collection import GenericCollection, Pagination
from onegov.core.utils import toggle
from onegov.directory.models import DirectoryEntry
from onegov.form import as_internal_id
from sqlalchemy import and_, desc
from sqlalchemy.orm import object_session
from sqlalchemy.dialects.postgresql import array


class DirectoryEntryCollection(GenericCollection, Pagination):
    """ Provides a view on a directory's entries.

    The directory itself might be a natural place for lots of these methods
    to reside, but ultimately we want to avoid mixing the concerns of the
    directory model and this view-supporting collection.

    """

    def __init__(self, directory, type='*', keywords=None, page=0,
                 search_widget=None):
        super().__init__(object_session(directory))

        self.type = type
        self.directory = directory
        self.keywords = keywords or {}
        self.page = page
        self.search_widget = search_widget

    def __eq__(self, other):
        return self.type == other.type and self.page == other.page

    def subset(self):
        return self.query()

    @property
    def search(self):
        return self.search_widget and self.search_widget.name

    @property
    def search_query(self):
        return self.search_widget and self.search_widget.search_query

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
        cls = self.model_class

        query = super().query().filter_by(directory_id=self.directory.id)
        keywords = self.valid_keywords(self.keywords)

        def keyword_group(value):
            return value.split(':')[0]

        values = [
            ':'.join((keyword, value))
            for keyword in keywords
            for value in keywords[keyword]
        ]
        values.sort(key=keyword_group)

        values = [
            cls._keywords.has_any(array(group_values))
            for group, group_values in groupby(values, key=keyword_group)
        ]
        if values:
            query = query.filter(and_(*values))

        if self.directory.configuration.direction == 'desc':
            query = query.order_by(desc(cls.order))
        else:
            query = query.order_by(cls.order)

        if self.search_widget:
            query = self.search_widget.adapt(query)

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

    def available_filters(self, sort_choices=False, sortfunc=None):
        """ Retrieve the filters with their choices. Return by default in the
        order of how the are defined in the structrue.
        To filter alphabetically, set sort_choices=True. """
        keywords = tuple(
            as_internal_id(k)
            for k in self.directory.configuration.keywords or tuple()
        )
        fields = {f.id: f for f in self.directory.fields if f.id in keywords}

        def _sort(values):
            if not sort_choices:
                return values
            if not sortfunc:
                return sorted(values)
            return sorted(values, key=sortfunc)

        return (
            (k, fields[k].label, _sort([c.label for c in fields[k].choices]))
            for k in keywords if hasattr(fields[k], 'choices')
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

        return self.__class__(
            directory=self.directory,
            type=self.type,
            search_widget=self.search_widget,
            keywords=parameters)

    def without_keywords(self):
        return self.__class__(
            directory=self.directory,
            type=self.type,
            page=self.page,
            search_widget=self.search_widget
        )
