from __future__ import annotations

import html
import re

from lingua import IsoCode639_1, LanguageDetectorBuilder
from onegov.core.orm import find_models
from sqlalchemy import inspect
from unidecode import unidecode


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
SPECIAL_CHARACTER_TRANS = str.maketrans({
    'Ä': 'Ae',
    'Ö': 'Oe',
    'Ü': 'Ue',
    'ä': 'ae',
    'ö': 'oe',
    'ü': 'ue',
    # NOTE: While << and >> are more natural translations and is what
    #       unidecode will do, we will end up with something that is
    #       interpreted as a HTML tag by Postgres
    # FIXME: To make this more robust we probably should process
    #        `Markup` differently from `str`, and for non-`Markup` we
    #        remove any `<` and `>` from the input.
    '«': '',
    '»': '',
})


def language_from_locale(locale: str | None) -> str:
    if locale is None:
        return 'simple'
    return LANGUAGE_MAP.get(locale, 'simple')


def normalize_text(text: str) -> str:
    """ This does the same thing  as unidecode, except it special-cases
    umlaut translation for German text.
    """
    return unidecode(text.translate(SPECIAL_CHARACTER_TRANS))


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
    model: Any,
    order_by_polymorphic_identity: bool = False
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
        query = query.filter(mapper.polymorphic_on.in_({
            m.polymorphic_identity
            for m in mapper.self_and_descendants
            if issubclass(m.class_, Searchable)
        }))
        if order_by_polymorphic_identity:
            query = query.order_by(mapper.polymorphic_on)
    return query


def extract_hashtags(text: str) -> list[str]:
    return HASHTAG.findall(html.unescape(text))


class classproperty(Generic[T_co]):  # noqa: N801
    def __init__(self, f: Callable[[type[Any]], T_co]) -> None:
        if isinstance(f, classmethod):
            # unwrap classmethod decorator which is used for typing
            f = f.__func__  # type:ignore[unreachable]
        self.f = f

    def __get__(self, obj: object | None, owner: type[object]) -> T_co:
        return self.f(owner)


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
