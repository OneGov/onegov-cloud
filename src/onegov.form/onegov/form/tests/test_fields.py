import base64
import tempfile

from cgi import FieldStorage
from gzip import GzipFile
from io import BytesIO
from onegov.form import Form
from onegov.form.fields import CoordinateField, UploadField


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


def test_coordinate_field():
    field = CoordinateField().bind(Form(), 'coordinate')
    template = (
        '<input class="coordinate" id="coordinate" name="coordinate" '
        'type="text" value="{}">'
    )

    assert not field.data

    assert field.data.lat is None
    assert field.data.lon is None
    assert field() == template.format('')

    field.process_formdata(['47.05183585/8.30576869173879'])

    assert field.data.lat == 47.05183585
    assert field.data.lon == 8.30576869173879

    field.data.lat = '47.05183585'
    assert field.data.lat == 47.05183585

    field.data.lon = '8.30576869173879'
    assert field.data.lon == 8.30576869173879

    assert field() == template.format('47.05183585/8.30576869173879')
