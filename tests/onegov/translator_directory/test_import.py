
from onegov.translator_directory.cli import parse_language_field


def test_parsing_language_field():
    text = 'A, B'
    assert list(parse_language_field(text)) == ['A', 'B']

    text = 'A,B'
    assert list(parse_language_field(text)) == ['A', 'B']

    text = "Lang (A, B), Lang (2),Lang3"
    assert list(parse_language_field(text)) == [
        'Lang (A, B)', 'Lang (2)', 'Lang3'
    ]
