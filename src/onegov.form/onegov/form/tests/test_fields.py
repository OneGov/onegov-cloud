import re
import tempfile

from cgi import FieldStorage
from gzip import GzipFile
from io import BytesIO
from onegov.core.utils import dictionary_to_binary
from onegov.form import Form
from onegov.form.fields import HtmlField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import OrderedMultiCheckboxField
from onegov.form.fields import UploadField
from onegov.form.fields import PhoneNumberField
from onegov.form.validators import ValidPhoneNumber


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

    assert dictionary_to_binary(data) == b'foobar'


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


def test_html_field():
    form = Form()
    field = HtmlField()
    field = field.bind(form, 'html')

    field.data = ''
    assert 'class="editor"' in field()
    assert field.validate(form)

    field.data = '<script>alert(0)</script>'
    field.validate(form)
    assert '<script>' not in field.data


def test_phone_number_field():
    form = Form()
    field = PhoneNumberField()
    field = field.bind(form, 'phone_number')
    assert field.country == 'CH'
    assert field.validators[0].country == 'CH'

    field.data = ''
    assert field.formatted_data == ''
    assert field.validate(form)

    field.data = '791112233'
    assert field.formatted_data == '+41791112233'
    assert field.validate(form)

    field.data = 'abc'
    assert field.formatted_data == 'abc'
    assert not field.validate(form)

    form = Form()
    field = PhoneNumberField(country='DE')
    field = field.bind(form, 'phone_number')
    assert field.validators[0].country == 'DE'
    assert field.country == 'DE'

    form = Form()
    field = PhoneNumberField(validators=[ValidPhoneNumber(country='DE')])
    field = field.bind(form, 'phone_number')
    assert field.validators[0].country == 'DE'
