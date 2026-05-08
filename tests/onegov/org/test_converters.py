from __future__ import annotations

from onegov.org.converters import keywords_converter


def test_keywords_converter() -> None:
    converter = keywords_converter

    assert converter.encode(None) == ['']
    assert converter.encode('') == ['']  # type: ignore[arg-type]
    assert converter.encode({}) == ['']
    assert converter.encode({'k': ['v']}) == ['k:v']
    assert converter.encode({'k': ['v1', 'v2']}) == ['k:v1+k:v2']
    assert converter.encode({'k1': ['v1'], 'k2': ['v2']}) == ['k1:v1+k2:v2']
    assert converter.encode({' k1': ['v 1'], 'k2 ': [' v 2 ']}) == [
        ' k1:v 1+k2 : v 2 ']
    assert converter.encode({'+k1': ['v+1'], 'k2+': ['+v++2+']}) == [
        '++k1:v++1+k2++:++v++++2++']

    assert converter.decode(['']) is None
    assert converter.decode([None]) is None  # type: ignore[list-item]
    assert converter.decode(['k:v']) == {'k': ['v']}
    assert converter.decode(['k:v1+k:v2']) == {'k': ['v1', 'v2']}
    assert converter.decode(['k1:v1+k2:v2']) == {'k1': ['v1'], 'k2': ['v2']}
    assert converter.decode([' k1:v 1+k2 : v 2 ']) == {
        ' k1': ['v 1'], 'k2 ': [' v 2 ']}
    assert converter.decode(['++k1:v++1+k2++:++v++++2++']) == {
        '+k1': ['v+1'], 'k2+': ['+v++2+']}
