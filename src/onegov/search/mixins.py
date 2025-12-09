from __future__ import annotations

from onegov.search.utils import classproperty
from onegov.search.utils import extract_hashtags


from typing import Any, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import datetime
    from typing import Any as AnyRequest


class Searchable:
    """ Defines the interface required for an object to be searchable.

    Note that ``fts_id `` and ``fts_properties`` must be class
    properties, not instance properties. So do this::

        class X(Searchable):

            fts_properties = {}

    But do not do this::

        class X(Searchable):

            @property
            def fts_properties(self):
                return {}

    The rest of the properties may be normal properties.

    """

    if TYPE_CHECKING:
        # FIXME: Gross classproperty vs. ClassVar is a mess, we should
        #        consistently use one or the other
        fts_properties: ClassVar[dict[str, Any]]
        fts_id: ClassVar[str]
        fts_type_title: ClassVar[str | Callable[[AnyRequest], str]]
        __tablename__: ClassVar[str]

    # TODO: rename to fts_properties
    @classproperty  # type:ignore[no-redef]
    @classmethod
    def fts_properties(cls) -> dict[str, Any]:
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

    # FIXME: Replace this with `inspect(model).primary_key[0]`
    @classproperty  # type:ignore[no-redef]
    @classmethod
    def fts_id(cls) -> str:
        """ The name of the id attribute (not the actual value!).

        If you use this on an ORM model, be sure to use a primary key, all
        other properties are not available during deletion.

        """
        raise NotImplementedError

    @classproperty  # type:ignore[no-redef]
    @classmethod
    def fts_type_title(cls) -> str | Callable[[AnyRequest], str]:
        """ Returns the display name for this type of document or a callable
        which accepts the current request as a single positional argument and
        returns the display name.

        """
        # NOTE: This fallback should generally not be relied upon, but it's
        #       better if we have a bad name, rather than a crash, when we
        #       add a new type and forget to add a custom title.
        return cls.__name__  # pragma: no cover

    @property
    def fts_language(self) -> str:
        """ Defines the language of the object. By default 'auto' is used,
        which triggers automatic language detection. Automatic language
        detection is reasonably accurate if provided with enough text. Short
        texts are not detected easily.

        When 'auto' is used, expect some content to be misclassified. You
        should then search over all languages, not just the expected one.

        This property can be used to manually set the language.

        """
        return 'auto'

    @property
    def fts_access(self) -> str:
        """ Returns access level of the model. Defaults to `public`.

        """
        return getattr(self, 'access', 'public')

    @property
    def fts_public(self) -> bool:
        """ Returns True if the model is available to be found by the public.
        If false, only editors/admins will see this object in the search
        results.

        """
        raise NotImplementedError

    @property
    def fts_skip(self) -> bool:
        """ Returns True if the indexing of this specific model instance
        should be skipped. """
        return False

    @property
    def fts_suggestion(self) -> Sequence[str] | str:
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
    def fts_publication_start(self) -> datetime | None:
        """ Returns the date when the document should become public. """
        return getattr(self, 'publication_start', None)

    @property
    def fts_publication_end(self) -> datetime | None:
        """ Returns the date when the document should stop being public. """
        return getattr(self, 'publication_end', None)

    @property
    def fts_last_change(self) -> datetime | None:
        """
        Returns the date the document was created/last modified.

        Returning `None` indicates that the document's age/recency must not
        influence search ranking: the item should be treated as equally
        relevant regardless of how old it is.
        """
        return None

    @property
    def fts_tags(self) -> list[str] | None:
        """ Returns a list of tags associated with this content. """
        return None


class ORMSearchable(Searchable):
    """ Extends the default :class:`Searchable` class with sensible defaults
    for SQLAlchemy orm models.

    """

    if TYPE_CHECKING:
        # FIXME: Gross classproperty vs. ClassVar is a mess, we should
        #        consistently use one or the other
        fts_id: ClassVar[str]

    @classproperty  # type:ignore[no-redef]
    @classmethod
    def fts_id(cls) -> str:
        return 'id'

    @property
    def fts_last_change(self) -> datetime | None:
        return getattr(self, 'last_change', None)


class SearchableContent(ORMSearchable):
    """ Adds search to all classes using the core's content mixin:
    :class:`onegov.core.orm.mixins.content.ContentMixin`

    """

    fts_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
        'lead': {'type': 'localized', 'weight': 'B'},
        'text': {'type': 'localized', 'weight': 'C'}
    }

    @property
    def fts_public(self) -> bool:
        return True

    @property
    def fts_tags(self) -> list[str] | None:
        tags: list[str] = []

        for field in ('lead', 'text', 'description'):
            text = getattr(self, field, None)

            if text:
                tags.extend(tag.lstrip('#') for tag in extract_hashtags(text))

        return tags or None
