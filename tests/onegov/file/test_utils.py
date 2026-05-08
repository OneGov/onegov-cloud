from __future__ import annotations

from onegov.core.utils import module_path
from onegov.file.utils import content_type_from_fileobj, word_count


def test_content_type_from_fileobj() -> None:

    def fixture(name: str) -> str:
        return module_path('tests.onegov.file', f'fixtures/{name}')

    def content_type(name: str) -> str:
        with open(fixture(name), 'rb') as f:
            return content_type_from_fileobj(f)

    assert content_type('example.pdf') == 'application/pdf'
    assert content_type('example.docx') == (
        'application/vnd.openxmlformats-'
        'officedocument.wordprocessingml.document'
    )


def test_word_count() -> None:
    assert word_count("") == 0
    assert word_count("foo bar") == 2
    assert word_count("It's simple really") == 3
