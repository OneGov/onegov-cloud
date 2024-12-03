import hashlib
import html
import os
import re

from onegov.core.custom import json
from langdetect import DetectorFactory, PROFILES_DIRECTORY
from langdetect.utils.lang_profile import LangProfile
from onegov.core.orm import find_models


from typing import Any, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from langdetect.detector import Detector
    from langdetect.language import Language
    from onegov.search.mixins import Searchable


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)


# XXX this is doubly defined in onegov.org.utils, maybe move to a common
# regex module in in onegov.core
HASHTAG = re.compile(r'(?<![\w/])#\w{3,}')


def searchable_sqlalchemy_models(
    base: type[T]
) -> 'Iterator[type[Searchable]]':
    """ Searches through the given SQLAlchemy base and returns the classes
    of all SQLAlchemy models found which inherit from the
    :class:`onegov.search.mixins.Searchable` interface.

    """

    # XXX circular imports
    from onegov.search import Searchable

    yield from find_models(  # type:ignore[misc]
        base, lambda cls: issubclass(cls, Searchable)
    )


def filter_non_base_models(models: 'set[type[T]]') -> 'set[type[T]]':
    """ Remove model classes that are base classes of other models in the set.
    Args: models: set of model classes to filter
    Returns: set: Model classes that are not base classes of any other model
    in the set.

    """
    non_base_models = set()

    for model in models:
        is_base = False
        for other_model in models:
            if model is not other_model and issubclass(other_model, model):
                is_base = True
                break

        if not is_base:
            non_base_models.add(model)

    return non_base_models


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


def hash_mapping(mapping: dict[str, Any]) -> str:
    dump = json.dumps(mapping, sort_keys=True).encode('utf-8')
    return hashlib.new('sha1', dump, usedforsecurity=False).hexdigest()


def extract_hashtags(text: str) -> list[str]:
    return [t.lower() for t in HASHTAG.findall(html.unescape(text))]


class classproperty(Generic[T_co]):  # noqa: N801
    def __init__(self, f: 'Callable[[type[Any]], T_co]') -> None:
        if isinstance(f, classmethod):
            # unwrap classmethod decorator which is used for typing
            f = f.__func__  # type:ignore[unreachable]
        self.f = f

    def __get__(self, obj: object | None, owner: type[object]) -> T_co:
        return self.f(owner)


def iter_subclasses(baseclass: type[T]) -> 'Iterator[type[T]]':
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
    """ Detects languages with the help of langdetect.

    Unlike langdetect this detector may be limited to a subset of all
    supported languages, which may improve accuracy if the subset is known and
    saves some memory.

    """

    def __init__(self, supported_languages: 'Sequence[str]') -> None:
        self.supported_languages = supported_languages
        self.factory = DetectorFactory()

        for ix, language in enumerate(supported_languages):
            path = os.path.join(PROFILES_DIRECTORY, language)

            with open(path, encoding='utf-8') as f:
                profile = LangProfile(**json.load(f))
                self.factory.add_profile(profile, ix, len(supported_languages))

    def spawn_detector(self, text: str) -> 'Detector':
        detector = self.factory.create()
        detector.append(text)

        return detector

    def detect(self, text: str) -> str:
        return self.spawn_detector(text).detect()

    def probabilities(self, text: str) -> list['Language']:
        return self.spawn_detector(text).get_probabilities()
