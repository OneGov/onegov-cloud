from __future__ import annotations

from cgi import FieldStorage
from onegov.file import NamedFile
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from tempfile import TemporaryFile


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob.request import _FieldStorageWithFile


def create_file(
    mimetype: str,
    filename: str,
    content: bytes
) -> _FieldStorageWithFile:

    fs = FieldStorage()
    fs.file = TemporaryFile("wb+")
    fs.type = mimetype
    fs.filename = filename
    fs.file.write(content)
    fs.file.seek(0)
    return fs  # type: ignore[return-value]


def test_named_file_form() -> None:

    class MyModel:
        files = []
        text = NamedFile()

    class MyForm(NamedFileForm):
        text = UploadField()

    form = MyForm()
    model = MyModel()
    form.populate_obj(model)
    form.process_obj(model)

    assert form.file_fields == {'text': form.text}
    assert form.get_useful_data() == {}

    textfile = create_file('text/plain', 'foo.txt', b'foo')
    form.text.data = form.text.process_fieldstorage(textfile)
    assert form.get_useful_data()['text'][0].read() == b'foo'
    assert form.get_useful_data()['text'][1] == 'foo.txt'

    assert form.text.file is not None
    form.text.file.seek(0)
    form.text.action = 'replace'
    form.populate_obj(model)
    assert model.text is not None
    assert model.text.reference.file.filename == 'foo.txt'
    assert model.text.reference.content_type == 'text/plain'
    assert model.text.reference.file.read() == b'foo'

    form = MyForm()
    form.process_obj(model)
    assert form.text.data == {
        'filename': 'foo.txt',
        'size': 3,
        'mimetype': 'text/plain'
    }

    form.text.action = 'delete'
    form.populate_obj(model)
    assert model.text is None
