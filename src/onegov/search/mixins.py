from __future__ import annotations

from onegov.search.utils import classproperty
from onegov.search.utils import extract_hashtags


from typing import Any, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime


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

    if TYPE_CHECKING:
        # FIXME: Gross classproperty vs. ClassVar is a mess, we should
        #        consistently use one or the other
        es_properties: ClassVar[dict[str, Any]]
        es_type_name: ClassVar[str]
        es_id: ClassVar[str]

    # TODO: rename to fts_properties
    @classproperty  # type:ignore[no-redef]
    @classmethod
    def es_properties(cls) -> dict[str, Any]:
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

    @classproperty  # type:ignore[no-redef]
    @classmethod
    def es_type_name(cls) -> str:
        """ Returns the unique type name of the model. """
        raise NotImplementedError

    @classproperty  # type:ignore[no-redef]
    @classmethod
    def es_id(cls) -> str:
        """ The name of the id attribute (not the actual value!).

        If you use this on an ORM model, be sure to use a primary key, all
        other properties are not available during deletion.

        """
        raise NotImplementedError

    @property
    def es_language(self) -> str:
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
    def es_public(self) -> bool:
        """ Returns True if the model is available to be found by the public.
        If false, only editors/admins will see this object in the search
        results.

        """
        raise NotImplementedError

    @property
    def es_skip(self) -> bool:
        """ Returns True if the indexing of this specific model instance
        should be skipped. """
        return False

    @property
    def es_suggestion(self) -> Sequence[str] | str:
        """ Returns suggest-as-you-type value of the document.
        The field used for this property should also be indexed, or the
        suggestion will lead to nowhere.

        If a single string is returned, the completion input equals the
        completion output. (My Title -> My Title)

        If an array of strings is returned, all values are possible inputs and
        the first value is the output. (My Title/Title My -> My Title)

        """
        return self.title  # type:ignore[attr-defined]

    @property
    def es_last_change(self) -> datetime | None:
        """ Returns the date the document was created/last modified. """
        return None

    @property
    def es_tags(self) -> list[str] | None:
        """ Returns a list of tags associated with this content. """
        return None


class ORMSearchable(Searchable):
    """ Extends the default :class:`Searchable` class with sensible defaults
    for SQLAlchemy orm models.

    """

    if TYPE_CHECKING:
        # FIXME: Gross classproperty vs. ClassVar is a mess, we should
        #        consistently use one or the other
        es_id: ClassVar[str]
        es_type_name: ClassVar[str]

    @classproperty  # type:ignore[no-redef]
    @classmethod
    def es_id(cls) -> str:
        return 'id'

    @classproperty  # type:ignore[no-redef]
    @classmethod
    def es_type_name(cls) -> str:
        return cls.__tablename__  # type:ignore[attr-defined]

    @property
    def es_last_change(self) -> datetime | None:
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
    def es_public(self) -> bool:
        return self.access == 'public'  # type:ignore[attr-defined]

    @property
    def es_suggestions(self) -> dict[str, list[str]]:
        return {
            'input': [self.title.lower()]  # type:ignore[attr-defined]
        }

    @property
    def es_tags(self) -> list[str] | None:
        tags: list[str] = []

        for field in ('lead', 'text', 'description'):
            text = getattr(self, field, None)

            if text:
                tags.extend(tag.lstrip('#') for tag in extract_hashtags(text))

        return tags or None
