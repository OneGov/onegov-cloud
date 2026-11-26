from __future__ import annotations

from onegov.search.utils import (
    classproperty,
    extract_hashtags,
    language_from_locale,
)


from typing import Any


def test_language_from_locale() -> None:
    assert language_from_locale(None) == 'simple'
    # any locale maps to a language string (unknown -> 'simple')
    assert isinstance(language_from_locale('xx_XX'), str)
    assert language_from_locale('xx_XX') == 'simple'


def test_extract_hashtags() -> None:
    assert extract_hashtags('Hello #world #foobar') == ['#world', '#foobar']
    # fewer than three characters are not matched
    assert extract_hashtags('#ab is too short') == []
    assert extract_hashtags('no tags here') == []


def test_classproperty() -> None:
    class Example:
        @classproperty
        def kind(cls: type[Any]) -> Any:  # noqa: N805
            return cls.__name__

    assert Example.kind == 'Example'
