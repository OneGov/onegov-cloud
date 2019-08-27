import onegov.file

from onegov.core.utils import module_path
from onegov.file.utils import content_type_from_fileobj, word_count


def test_content_type_from_fileobj():

    def fixture(name):
        return module_path(onegov.file, f'tests/fixtures/{name}')

    def content_type(name):
        with open(fixture(name), 'rb') as f:
            return content_type_from_fileobj(f)

    assert content_type('example.pdf') == 'application/pdf'
    assert content_type('example.docx') == (
        'application/vnd.openxmlformats-'
        'officedocument.wordprocessingml.document'
    )


def test_word_count():
    assert word_count("") == 0
    assert word_count("foo bar") == 2
    assert word_count("It's simple really") == 3
