import base64
import re
import tempfile

from cgi import FieldStorage
from gzip import GzipFile
from io import BytesIO
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import OrderedMultiCheckboxField
from onegov.form.fields import UploadField


def create_file(mimetype, filename, content):
    fs = FieldStorage()
    fs.file = tempfile.TemporaryFile("wb+")
    fs.type = mimetype
    fs.filename = filename
    fs.file.write(content)
    fs.file.seek(0)
    return fs


def test_upload_file():
    field = UploadField()
    field = field.bind(Form(), 'upload')

    textfile = create_file('text/plain', 'test.txt', b'foobar')
    data = field.process_fieldstorage(textfile)

    assert data['filename'] == 'test.txt'
    assert data['mimetype'] == 'text/plain'
    assert data['size']
    assert data['data']

    def decompress(data):
        with GzipFile(filename='', mode='r', fileobj=BytesIO(data)) as f:
            return f.read()

    assert decompress(base64.b64decode(data['data'])) == b'foobar'


def test_ordered_multi_checkbox_field():
    ordinary = MultiCheckboxField(choices=[
        ('c', 'C'),
        ('b', 'B'),
        ('a', 'A')
    ])
    ordered = OrderedMultiCheckboxField(choices=[
        ('c', 'C'),
        ('b', 'B'),
        ('a', 'A')
    ])
    ordinary = ordinary.bind(Form(), 'choices')
    ordered = ordered.bind(Form(), 'choices')

    ordinary.data = ordered.data = []

    assert re.findall(r'value="((a|b|c){1})"', ordinary()) == [
        ('c', 'c'),
        ('b', 'b'),
        ('a', 'a'),
    ]

    assert re.findall(r'value="((a|b|c){1})"', ordered()) == [
        ('a', 'a'),
        ('b', 'b'),
        ('c', 'c'),
    ]
