import re
import tempfile

from cgi import FieldStorage
from datetime import datetime
from gzip import GzipFile
from io import BytesIO


from onegov.core.utils import dictionary_to_binary
from onegov.form import Form
from onegov.form.fields import ChosenSelectField, DateTimeLocalField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import HtmlField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import OrderedMultiCheckboxField
from onegov.form.fields import PhoneNumberField
from onegov.form.fields import UploadField
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

    textfile = create_file('text/plain', 'C:/mydata/test.txt', b'foobar')
    data = field.process_fieldstorage(textfile)
    assert data['filename'] == 'test.txt'

    def decompress(data):
        with GzipFile(filename='', mode='r', fileobj=BytesIO(data)) as f:
            return f.read()

    assert dictionary_to_binary(data) == b'foobar'


def test_multi_checkbox_field_disabled():
    form = Form()
    field = MultiCheckboxField(
        choices=(('a', 'b'),),
        render_kw={'disabled': True}
    )
    field = field.bind(form, 'choice')

    field.data = ''
    assert 'input disabled' in field()


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


def test_chosen_select_field():
    form = Form()
    field = ChosenSelectField(choices=(('a', 'b'),))
    field = field.bind(form, 'choice')

    field.data = ''
    assert 'class="chosen-select"' in field()
    assert 'data-no_results_text="No results match"' in field()
    assert 'data-placeholder="Select an Option"' in field()


def test_chosen_select_multiple_field():
    form = Form()
    field = ChosenSelectMultipleField(choices=(('a', 'b'),))
    field = field.bind(form, 'choice')

    field.data = ''
    assert 'class="chosen-select"' in field()
    assert 'data-no_results_text="No results match"' in field()
    assert 'data-placeholder="Select Some Options"' in field()


def test_date_time_local_field():

    class DummyPostData(dict):
        def getlist(self, key):
            v = self[key]
            if not isinstance(v, (list, tuple)):
                v = [v]
            return v

    form = Form()
    field = DateTimeLocalField()
    field = field.bind(form, 'dt')

    assert field.format == '%Y-%m-%dT%H:%M'
    field.data = datetime(2010, 1, 2, 3, 4)
    assert "2010-01-02T03:04" in field()

    field = DateTimeLocalField()
    field = field.bind(form, 'dt')

    field.process(DummyPostData({'dt': "2010-01-02T03:04"}))
    assert field.data == datetime(2010, 1, 2, 3, 4)

    field.process(DummyPostData({'dt': "2010-05-06 07:08"}))
    assert field.data == datetime(2010, 5, 6, 7, 8)

    # Firefox...
    field.process(DummyPostData({'dt': "2010-05-06 07:08:00"}))
    assert field.data == datetime(2010, 5, 6, 7, 8)
