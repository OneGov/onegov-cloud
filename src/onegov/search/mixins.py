from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import deferred

from onegov.core.orm.mixins import content
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

    if TYPE_CHECKING:
        fts_idx: 'Column[dict[str, Any]]'

    # column for full text search index
    @declared_attr  # type:ignore[no-redef]
    def fts_idx(cls) -> 'Column[dict[str, Any]]':
        if hasattr(cls, '__table__') and hasattr(cls.__table__.c, 'fts_idx'):
            return deferred(cls.__table__.c.fts_idx)
        # return deferred(Column(TSVECTOR, index=True))
        return deferred(Column(TSVECTOR))

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
    def psql_tsvector_string(model):
        """
        Provides the tsvector string for postgres defining which columns and
        json fields to be used for full text search index.

        Example:
        s = create_tsvector_string('title', 'location')
        s += " || ' ' || coalesce(((content ->> 'description')), '')"
        s += " || ' ' || coalesce(((content ->> 'organizer')), '')"

        :return: tsvector string
        """

        join = " || ' ' || "

        # identify search columns
        columns = [p for p in model.es_properties if p in model.__dict__ and
                   not p.startswith('es_') and
                   isinstance(model.__dict__[p], (InstrumentedAttribute,
                                                  property, hybrid_property))]
        s = Searchable.create_tsvector_string(*columns) if columns else ''
        print(f'*** tschupre tsvector string columns: {columns}')

        # identify content and meta properties
        for p in model.es_properties:
            if p in model.__dict__ and isinstance(model.__dict__[p],
                                                  content.dict_property):
                s += join if s else ''
                s += f"coalesce((({model.__dict__[p].attribute} " \
                     f"->> '{p}')), '')"

        return s

    @staticmethod
    def reindex(session, schema, model):
        """
        Re-indexes the table by dropping and adding the full text search
        column.
        """
        Searchable.drop_fts_column(session, schema, model)
        Searchable.add_fts_column(session, schema, model)

    @staticmethod
    def drop_fts_column(session, schema, model, col_name='fts_idx'):
        """
        Drops the full text search column

        :param session: db session
        :param schema: schema the full text column shall be added
        :param model: model to drop the index from
        :param col_name: column name of fts index
        :return: None
        """
        query = f"""
            ALTER TABLE "{schema}".{model.__tablename__} DROP COLUMN IF EXISTS
            {col_name};
        """
        session.execute(query)
        session.execute("COMMIT")

    @staticmethod
    def add_fts_column(session, schema, model, col_name='fts_idx'):

        """
        This function is used for re-indexing and as migration step moving to
        postgresql full text search (fts), OGC-508.

        It adds a separate column for the tsvector to `schema`.`table`
        creating a multilingual gin index on the columns/data defined per
        model.

        :param session: session
        :param schema: schema name
        :param model: model to add the index
        :param col_name: column name of fts index
        :return: None
        """

        # we build the tsvector expression for all supported languages based
        # on this format
        # to_tsvector('simple', '<tsvector_string_of_model') ||
        # to_tsvector('german', '<tsvector_string_of_model') ||
        # to_tsvector('french', '<tsvector_string_of_model') ||
        # ...

        print(f'*** tschurpe reindexing {model}..')
        tsvector_expression = \
            Searchable.multi_language_tsvector_expression(
                model.psql_tsvector_string(model))

        query = f"""
            ALTER TABLE "{schema}".{model.__tablename__}
            ADD COLUMN IF NOT EXISTS {col_name} tsvector GENERATED ALWAYS AS
            ({tsvector_expression}) STORED;
        """
        session.execute(query)
        session.execute("COMMIT")

    @staticmethod
    def multi_language_tsvector_expression(tsvector_string):
        return ' || '.join(
            "to_tsvector('{}', {})".format(language, tsvector_string)
            for language in get_fts_index_languages()
        )

    @staticmethod
    def create_tsvector_string(*cols):
        """
        Creates tsvector string for columns
        Doc reference:
        https://www.postgresql.org/docs/current/textsearch-tables.html#TEXTSEARCH-TABLES-INDEX

        :param cols: column names to be indexed
        :return: tsvector string for multiple columns i.e. for columns title
        and body: coalesce(\"title\", '') || ' ' || coalesce(\"body\", '')
        Note that the '\"{}\"' escapes the column name in case it is a
        keyword, see
        http://www.postgresql.org/docs/current/static/sql-keywords-appendix.html
        """
        base = "coalesce(\"{}\", '')"
        ext = " || ' ' || coalesce(\"{}\", '')"

        s = base
        for _ in range(len(cols) - 1):
            s += ext

        return s.format(*cols)


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
