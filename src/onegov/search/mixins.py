from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred
from typing import Any

from onegov.search.utils import classproperty
from onegov.search.utils import extract_hashtags


# TODO: generalize to 'fts' instead of 'es'
class Searchable:
    """ Defines the interface required for an object to be searchable.

    Note that ``es_id ``, ``es_properties`` and ``es_type_name`` must be class
    properties, not instance properties. So do this::

        class X(Searchable):

            es_properties = {}
            es_type_name = 'x'

    But do not do this::

        class X(Searchable):

            @property
            def es_properties(self):
                return {}

            @property
            def es_type_name(self):
                return 'x'

    The rest of the properties may be normal properties.

    **Polymorphic Identities**

    If SQLAlchemy's Polymorphic Identities are used, each identity must
    have it's own unqiue ``es_type_name``. Though such models may share
    the ``es_properties`` from the base class, we don't assume anything and
    store each polymorphic identity in its own index.

    From the point of view of elasticsearch, each different polymorphic
    identity is a completely different model.

    """

    TEXT_SEARCH_COLUMN_NAME = 'fts_idx'
    TEXT_SEARCH_DATA_COLUMN_NAME = 'fts_idx_data'

    @declared_attr
    def fts_idx(cls) -> 'Column[dict[str, Any]]':
        """ The column for the full text search index.
        """

        col_name = Searchable.TEXT_SEARCH_COLUMN_NAME
        if hasattr(cls, '__table__') and hasattr(cls.__table__.c, col_name):
            return deferred(cls.__table__.c.fts_idx)
        return deferred(Column(col_name, TSVECTOR))

    @declared_attr
    def fts_idx_data(cls) -> 'Column[str]':
        """ The data column acts as input for the full text search index.
        Collected from columns and properties of the model,
        see `gather_fts_index_data`. The fts index is built on this column.

        NOTE: postgres does not allow to index obj by obj, only columns.

        """
        col_name = cls.TEXT_SEARCH_DATA_COLUMN_NAME
        if hasattr(cls, '__table__') and hasattr(cls.__table__.c, col_name):
            return deferred(cls.__table__.c.fts_idx_data)
        return deferred(Column(col_name, Text))

    def gather_fts_index_data(self) -> str:
        """ Collects the full text search (fts) index data based on columns
        and properties as specified in fts_properties. This data is the basis
        for the fts index.
        """

        data = []
        for prop_name, type_info in self.es_properties.items():
            if not prop_name.startswith('es_'):
                attr = getattr(self, prop_name, '')
                if not attr:
                    continue

                if isinstance(attr, list):
                    data.extend([str(a) for a in attr])
                elif isinstance(attr, dict):
                    data.extend([str(a) for a in attr.values()])
                elif isinstance(attr, set):
                    data.extend([str(a) for a in attr])
                else:
                    data.append(str(attr))

        return ' '.join(data)

    # TODO: rename to fts_properties
    @classproperty
    def es_properties(self):
        """ Returns the type mapping of this model. Each property in the
        mapping will be read from the model instance.

        The returned object needs to be a dict or an object that provides
        a ``to_dict`` method.

        Internally, onegov.search stores differing languages in different
        indices. It does this automatically through langauge detection, or
        by manually specifying a language.

        Note that objects with multiple languages are not supported
        (each object is supposed to have exactly one language).

        Onegov.search will automatically insert the right analyzer for
        types like these.

        There's currently only limited support for properties here, namely
        objects and nested mappings do not work! This is going to be added
        in the future though.

        """
        raise NotImplementedError

    @classproperty
    def es_type_name(self):
        """ Returns the unique type name of the model. """
        raise NotImplementedError

    @classproperty
    def es_id(self):
        """ The name of the id attribute (not the actual value!).

        If you use this on an ORM model, be sure to use a primary key, all
        other properties are not available during deletion.

        """
        raise NotImplementedError

    @property
    def es_language(self):
        """ Defines the language of the object. By default 'auto' is used,
        which triggers automatic language detection. Automatic language
        detection is reasonably accurate if provided with enough text. Short
        texts are not detected easily.

        When 'auto' is used, expect some content to be misclassified. You
        should then search over all languages, not just the epxected one.

        This property can be used to manually set the language.

        """
        return 'auto'

    # TODO: rename to fts_public
    @property
    def es_public(self):
        """ Returns True if the model is available to be found by the public.
        If false, only editors/admins will see this object in the search
        results.

        """
        raise NotImplementedError

    @property
    def es_skip(self):
        """ Returns True if the indexing of this specific model instance
        should be skipped. """
        return False

    @property
    def es_suggestion(self):
        """ Returns suggest-as-you-type value of the document.
        The field used for this property should also be indexed, or the
        suggestion will lead to nowhere.

        If a single string is returned, the completion input equals the
        completion output. (My Title -> My Title)

        If an array of strings is returned, all values are possible inputs and
        the first value is the output. (My Title/Title My -> My Title)

        """
        return self.title

    @property
    def es_last_change(self):
        """ Returns the date the document was created/last modified. """
        return None

    @property
    def es_tags(self):
        """ Returns a list of tags associated with this content. """
        return None


class ORMSearchable(Searchable):
    """ Extends the default :class:`Searchable` class with sensible defaults
    for SQLAlchemy orm models.

    """

    @classproperty
    def es_id(self):
        return 'id'

    @classproperty
    def es_type_name(self):
        return self.__tablename__

    @property
    def es_last_change(self):
        return getattr(self, 'last_change', None)


class SearchableContent(ORMSearchable):
    """ Adds search to all classes using the core's content mixin:
    :class:`onegov.core.orm.mixins.content.ContentMixin`

    """

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
        'text': {'type': 'localized_html'}
    }

    @property
    def es_public(self):
        return self.access == 'public'

    @property
    def es_suggestions(self):
        return {
            "input": [self.title.lower()]
        }

    @property
    def es_tags(self):
        tags = []

        for field in ('lead', 'text', 'description'):
            text = getattr(self, field, None)

            if text:
                tags.extend(tag.lstrip('#') for tag in extract_hashtags(text))

        return tags or None
