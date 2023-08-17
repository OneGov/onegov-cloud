from sqlalchemy import Column, func, Computed  # type:ignore[attr-defined]
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred

from onegov.core.upgrade import UpgradeContext
from onegov.search.utils import classproperty, get_fts_index_languages
from onegov.search.utils import extract_hashtags

from typing import Any, TYPE_CHECKING


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

    if TYPE_CHECKING:
        fts_idx: 'Column[dict[str, Any]]'

    # column for full text search index
    @declared_attr  # type:ignore[no-redef]
    def fts_idx(cls) -> 'Column[dict[str, Any]]':
        col_name = Searchable.TEXT_SEARCH_COLUMN_NAME
        if hasattr(cls, '__table__') and hasattr(cls.__table__.c, col_name):
            return deferred(cls.__table__.c.fts_idx)
        return deferred(Column(col_name, TSVECTOR))

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

    @property
    def search_score(self):
        """
        the lower the score the higher the class type will be shown in search
        results. Default is 10 (lowest)
        """
        return 10

    @staticmethod
    def psql_tsvector_expression(model):
        """
        Provides the tsvector expression for postgres for the defined
        model. Depending on the model columns and properties are used for full
        text search index.

        :return: tsvector expression
        """
        objects = [getattr(model, p) for p in model.es_properties if
                   not p.startswith('es_')]
        return Searchable.create_tsvector_expression(*objects)

    @staticmethod
    def reindex(request, model):
        """
        Re-indexes the table by dropping and adding the full text search
        column.
        """
        Searchable.drop_fts_column(request, model)
        Searchable.add_fts_column(request, model)

    @staticmethod
    def drop_fts_column(request, model):
        """
        Drops the full text search column

        :param request: request object
        :param model: model to drop the index from
        :return: None
        """

        col_name = Searchable.TEXT_SEARCH_COLUMN_NAME
        context = UpgradeContext(request)

        if context.has_column(model.__tablename__, col_name):
            context.operations.drop_column(model.__tablename__, col_name)

    @staticmethod
    def add_fts_column(request, model):

        """
        This function is used for re-indexing and as migration step moving to
        postgresql full text search (fts), OGC-508.

        It adds a separate column for the tsvector to `schema`.`table`
        creating a multilingual gin index on the columns/data defined per
        model.

        :param request: request object
        :param model: model to add the index
        :return: None
        """

        col_name = Searchable.TEXT_SEARCH_COLUMN_NAME
        context = UpgradeContext(request)
        if not context.has_column(model.__tablename__, col_name):
            tsvector_expression = \
                Searchable.multi_language_tsvector_expression(
                    model.psql_tsvector_expression(model))

            context.operations.add_column(
                model.__tablename__,
                Column(col_name,
                       TSVECTOR,
                       Computed(
                           tsvector_expression,
                           persisted=True),
                       )
            )
            context.operations.execute("COMMIT")

    @staticmethod
    def multi_language_tsvector_expression(tsvector_expression):
        """
        build the tsvector expression for all supported languages based
        on this format

        :param tsvector_expression:
        :return: multilingual tsvector expression
        """

        language = get_fts_index_languages()[0]
        expr = func.to_tsvector(language, tsvector_expression)

        for language in get_fts_index_languages()[1:]:
            expr = expr.concat(' ')
            expr = expr.concat(func.to_tsvector(language, tsvector_expression))

        return expr

    @staticmethod
    def create_tsvector_expression(*cols):
        """
        Creates tsvector expression for columns/properties

        Doc reference:
        https://www.postgresql.org/docs/current/textsearch-tables.html#TEXTSEARCH-TABLES-INDEX

        :param cols: column names / properties to be indexed
        :return: tsvector expression for multiple columns / properties

        """
        assert len(cols) >= 1, "Need to provide at least one column"

        first_col, *remaining_cols = cols
        expr = func.coalesce(first_col, '')
        for col in remaining_cols:
            expr = expr.concat(' ')
            expr = expr.concat(func.coalesce(col, ''))

        return expr


# TODO: rename prefix 'es' to 'ts' for text search
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


# TODO: rename prefix 'es' to 'ts' for text search
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
