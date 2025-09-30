from __future__ import annotations

import html
import re

from sqlalchemy import inspect
from lingua import IsoCode639_1, LanguageDetectorBuilder
from onegov.core.orm import find_models


from typing import Any, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from lingua import ConfidenceValue
    from onegov.core.orm import Base
    from onegov.search.mixins import Searchable
    from sqlalchemy.orm import Query


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)


# XXX this is doubly defined in onegov.org.utils, maybe move to a common
# regex module in in onegov.core
HASHTAG = re.compile(r'(?<![\w/])#\w{3,}')
LANGUAGE_MAP = {
    'de_CH': 'german',
    'de': 'german',
    'fr_CH': 'french',
    'fr': 'french',
    'it_CH': 'italian',
    'it': 'italian',
    'rm_CH': 'english',
    'rm': 'english',
}


def language_from_locale(locale: str | None) -> str:
    if locale is None:
        return 'simple'
    return LANGUAGE_MAP.get(locale, 'simple')


def searchable_sqlalchemy_models(
    base: type[T]
) -> Iterator[type[Searchable]]:
    """ Searches through the given SQLAlchemy base and returns the classes
    of all SQLAlchemy models found which inherit from the
    :class:`onegov.search.mixins.Searchable` interface.

    """

    # XXX circular imports
    from onegov.search import Searchable

    yield from find_models(  # type:ignore[misc]
        base, lambda cls: issubclass(cls, Searchable)
    )


def get_polymorphic_base(
    model: type[Searchable]
) -> type[Base | Searchable]:
    """
    Filter out models that are polymorphic subclasses of other
    models in order to save on queries.

    """
    mapper = inspect(model)
    if mapper.polymorphic_on is None:
        return model
    return mapper.base_mapper.class_


def apply_searchable_polymorphic_filter(
    query: Query[T],
    model: Any
) -> Query[T]:
    """
    Given a query and the corresponding model add a filter
    that excludes any polymorphic variants, that are not
    searchable.
    """

    # XXX circular imports
    from onegov.search import Searchable

    mapper = inspect(model)
    if mapper.polymorphic_on is not None:
        # only include the polymorphic identities that
        # are actually searchable
        return query.filter(mapper.polymorphic_on.in_({
            m.polymorphic_identity
            for m in mapper.self_and_descendants
            if issubclass(m.class_, Searchable)
        }))
    return query


_invalid_index_characters = re.compile(r'[\\/?"<>|\s,A-Z:]+')


def is_valid_index_name(name: str) -> bool:
    """ Checks if the given name is a valid elasticsearch index name.
    Elasticsearch does it's own checks, but we can do it earlier and we are
    a bit stricter.

    """

    if name.startswith(('_', '.')):
        return False

    if _invalid_index_characters.search(name):
        return False

    if '*' in name:
        return False

    return True


def is_valid_type_name(name: str) -> bool:
    # the type name may be part of the index name, so we use the same check
    return is_valid_index_name(name)


def normalize_index_segment(segment: str, allow_wildcards: bool) -> str:
    valid = _invalid_index_characters.sub('_', segment.lower())

    if not allow_wildcards:
        valid = valid.replace('*', '_')

    return valid.replace('.', '_').replace('-', '_')


def extract_hashtags(text: str) -> list[str]:
    return [t.lower() for t in HASHTAG.findall(html.unescape(text))]


class classproperty(Generic[T_co]):  # noqa: N801
    def __init__(self, f: Callable[[type[Any]], T_co]) -> None:
        if isinstance(f, classmethod):
            # unwrap classmethod decorator which is used for typing
            f = f.__func__  # type:ignore[unreachable]
        self.f = f

    def __get__(self, obj: object | None, owner: type[object]) -> T_co:
        return self.f(owner)


def iter_subclasses(baseclass: type[T]) -> Iterator[type[T]]:
    for subclass in baseclass.__subclasses__():
        yield subclass

        # FIXME: Why are we only iterating two levels of inheritance?
        yield from subclass.__subclasses__()


def related_types(model: type[object]) -> set[str]:
    """ Gathers all related es type names from the given model. A type is
    counted as related a model is part of a polymorphic setup.

    If no polymorphic identity is found, the result is simply a set with the
    model's type itself.

    """

    if type_name := getattr(model, 'es_type_name', None):
        result = {type_name}
    else:
        result = set()

    if hasattr(model, '__mapper_args__'):
        if 'polymorphic_on' in model.__mapper_args__:
            for subclass in iter_subclasses(model):
                if type_name := getattr(subclass, 'es_type_name', None):
                    result.add(type_name)

        elif 'polymorphic_identity' in model.__mapper_args__:
            for parentclass in model.__mro__:
                if not hasattr(parentclass, '__mapper_args__'):
                    continue

                if 'polymorphic_on' in parentclass.__mapper_args__:
                    return related_types(parentclass)

    return result


class LanguageDetector:
    """ Detects languages with the help of lingua-language-detector.

    """

    def __init__(self, supported_languages: Sequence[str]) -> None:
        self.supported_languages = supported_languages
        self.detector = LanguageDetectorBuilder.from_iso_codes_639_1(*(
            IsoCode639_1.from_str(language)
            for language in supported_languages
        )).build()

    def detect(self, text: str) -> str:
        language = self.detector.detect_language_of(text)
        if language is None:
            # fallback to the first supported language
            return self.supported_languages[0]
        return language.iso_code_639_1.name.lower()

    def probabilities(self, text: str) -> list[ConfidenceValue]:
        return self.detector.compute_language_confidence_values(text)
