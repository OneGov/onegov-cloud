import onegov.file

from onegov.core.utils import module_path
from onegov.file.utils import content_type_from_fileobj


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
