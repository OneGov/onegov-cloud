import re
import tempfile

from cgi import FieldStorage
from datetime import datetime
from onegov.core.utils import Bunch
from onegov.core.utils import dictionary_to_binary
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import CssField
from onegov.form.fields import DateTimeLocalField
from onegov.form.fields import HoneyPotField
from onegov.form.fields import HtmlField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import OrderedMultiCheckboxField
from onegov.form.fields import PhoneNumberField
from onegov.form.fields import UploadField
from onegov.form.validators import ValidPhoneNumber
from unittest.mock import patch


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def create_file(mimetype, filename, content):
    fs = FieldStorage()
    fs.file = tempfile.TemporaryFile("wb+")
    fs.type = mimetype
    fs.filename = filename
    fs.file.write(content)
    fs.file.seek(0)
    return fs


def test_upload_field():
    def create_field():
        form = Form()
        field = UploadField()
        field = field.bind(form, 'upload')
        return form, field

    # Test process fieldstorage
    form, field = create_field()
    data = field.process_fieldstorage(None)
    assert data == {}
    assert field.file is None
    assert field.filename is None

    form, field = create_field()
    data = field.process_fieldstorage(b'')
    assert data == {}
    assert field.file is None
    assert field.filename is None

    textfile = create_file('text/plain', 'foo.txt', b'foo')
    data = field.process_fieldstorage(textfile)
    assert data['filename'] == 'foo.txt'
    assert data['mimetype'] == 'text/plain'
    assert data['size']
    assert data['data']
    assert dictionary_to_binary(data) == b'foo'
    assert field.filename == 'foo.txt'
    assert field.file.read() == b'foo'

    form, field = create_field()
    textfile = create_file('text/plain', 'C:/mydata/bar.txt', b'bar')
    data = field.process_fieldstorage(textfile)
    assert data['filename'] == 'bar.txt'
    assert data['mimetype'] == 'text/plain'
    assert data['size']
    assert data['data']
    assert dictionary_to_binary(data) == b'bar'
    assert field.filename == 'bar.txt'
    assert field.file.read() == b'bar'

    # Test rendering
    form, field = create_field()
    textfile = create_file('text/plain', 'baz.txt', b'baz')

    assert 'without-data' in field()

    field.data = field.process_fieldstorage(textfile)
    assert 'without-data' in field(force_simple=True)

    html = field()
    assert 'with-data' in html
    assert 'Uploaded file: baz.txt (3 Bytes) ✓' in html
    assert 'keep' in html
    assert 'type="file"' in html
    assert 'value="baz.txt"' not in html

    html = field(resend_upload=True)
    assert 'with-data' in html
    assert 'Uploaded file: baz.txt (3 Bytes) ✓' in html
    assert 'keep' in html
    assert 'type="file"' in html
    assert 'value="baz.txt"' in html

    # Test submit
    form, field = create_field()
    field.process(DummyPostData({}))
    assert field.validate(form)
    assert field.data == {}

    form, field = create_field()
    field.process(DummyPostData({'upload': 'abcd'}))
    assert field.validate(form)  # fails silently
    assert field.action == 'replace'
    assert field.data == {}
    assert field.file is None
    assert field.filename is None

    # ... simple
    form, field = create_field()
    textfile = create_file('text/plain', 'foobar.txt', b'foobar')
    field.process(DummyPostData({'upload': textfile}))
    assert field.validate(form)
    assert field.action == 'replace'
    assert field.data['filename'] == 'foobar.txt'
    assert field.data['mimetype'] == 'text/plain'
    assert field.data['size'] == 6
    assert dictionary_to_binary(field.data) == b'foobar'
    assert field.filename == 'foobar.txt'
    assert field.file.read() == b'foobar'

    # ... with select
    form, field = create_field()
    textfile = create_file('text/plain', 'foobar.txt', b'foobar')
    field.process(DummyPostData({'upload': ['keep', textfile]}))
    assert field.validate(form)
    assert field.action == 'keep'

    form, field = create_field()
    textfile = create_file('text/plain', 'foobar.txt', b'foobar')
    field.process(DummyPostData({'upload': ['delete', textfile]}))
    assert field.validate(form)
    assert field.action == 'delete'
    assert field.data == {}

    form, field = create_field()
    textfile = create_file('text/plain', 'foobar.txt', b'foobar')
    field.process(DummyPostData({'upload': ['replace', textfile]}))
    assert field.validate(form)
    assert field.action == 'replace'
    assert field.data['filename'] == 'foobar.txt'
    assert field.data['mimetype'] == 'text/plain'
    assert field.data['size']
    assert dictionary_to_binary(field.data) == b'foobar'
    assert field.filename == 'foobar.txt'
    assert field.file.read() == b'foobar'

    # ... with select and keep upload
    previous = field.data.copy()
    form, field = create_field()
    textfile = create_file('text/plain', 'foobaz.txt', b'foobaz')
    field.process(DummyPostData({'upload': [
        'keep',
        textfile,
        previous['filename'],
        previous['data']
    ]}))
    assert field.validate(form)
    assert field.action == 'keep'
    assert field.data['filename'] == 'foobar.txt'
    assert field.data['mimetype'] == 'text/plain'
    assert field.data['size'] == 6
    assert dictionary_to_binary(field.data) == b'foobar'

    field.process(DummyPostData({'upload': [
        'delete',
        textfile,
        previous['filename'],
        previous['data']
    ]}))
    assert field.validate(form)
    assert field.action == 'delete'
    assert field.data == {}

    field.process(DummyPostData({'upload': [
        'replace',
        textfile,
        previous['filename'],
        previous['data']
    ]}))
    assert field.validate(form)
    assert field.action == 'replace'
    assert field.data['filename'] == 'foobaz.txt'
    assert field.data['mimetype'] == 'text/plain'
    assert field.data['size'] == 6
    assert dictionary_to_binary(field.data) == b'foobaz'
    assert field.filename == 'foobaz.txt'
    assert field.file.read() == b'foobaz'


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


def test_honeypot_field():
    form = Form()
    form.request = Bunch(client_addr='1.1.1.1')
    field = HoneyPotField()
    field = field.bind(form, 'honeypot')
    field.meta.request = Bunch(include=lambda x: None)
    field.data = ''

    assert 'class="lazy-wolves"' in field()
    assert field.validate(form)

    field.data = 'me-a-stupid-bot'
    with patch('onegov.form.fields.log') as log:
        assert not field.validate(form)
        assert field.errors == ['Invalid value']
        log.info.assert_called_with('Honeypot used by 1.1.1.1')


def test_css_field():
    form = Form()
    field = CssField()
    field = field.bind(form, 'css')
    field.data = ''

    assert '<textarea id="css" name="css">' in field()
    assert field.validate(form)

    field.data = '* { x'
    assert not field.validate(form)
    assert field.errors

    field.data = '* { font-weight: bold }'
    assert field.validate(form)
    assert not field.errors
