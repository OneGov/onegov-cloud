import re
import tempfile

from cgi import FieldStorage
from copy import deepcopy
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
from onegov.form.fields import TranslatedSelectField
from onegov.form.fields import UploadField
from onegov.form.fields import UploadMultipleField
from onegov.form.fields import URLField
from onegov.form.validators import ValidPhoneNumber
from unittest.mock import patch
from wtforms.validators import Optional
from wtforms.validators import URL


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
    previous = field.data
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


def test_upload_multiple_field():
    def create_field():
        form = Form()
        field = UploadMultipleField()
        field = field.bind(form, 'uploads')
        return form, field

    # Test rendering and initial submit
    form, field = create_field()
    field.process(None)
    assert len(field) == 0

    html = field()
    assert 'without-data' in html
    assert 'multiple' in html
    assert 'name="uploads"' in html
    assert 'with-data' not in html
    assert 'name="uploads-0"' not in html

    file1 = create_file('text/plain', 'baz.txt', b'baz')
    file2 = create_file('text/plain', 'foobar.txt', b'foobar')
    field.process(DummyPostData({'uploads': [file1, file2]}))
    assert len(field.data) == 2
    assert field.data[0]['filename'] == 'baz.txt'
    assert field.data[0]['mimetype'] == 'text/plain'
    assert field.data[0]['size'] == 3
    assert field.data[1]['filename'] == 'foobar.txt'
    assert field.data[1]['mimetype'] == 'text/plain'
    assert field.data[1]['size'] == 6

    assert len(field) == 2
    file_field1, file_field2 = field
    assert file_field1.name == 'uploads-0'
    assert file_field1.action == 'replace'
    assert dictionary_to_binary(file_field1.data) == b'baz'
    assert file_field1.filename == 'baz.txt'
    assert file_field1.file.read() == b'baz'
    assert file_field2.name == 'uploads-1'
    assert file_field2.action == 'replace'
    assert dictionary_to_binary(file_field2.data) == b'foobar'
    assert file_field2.filename == 'foobar.txt'
    assert file_field2.file.read() == b'foobar'

    html = field(force_simple=True)
    assert 'without-data' in html
    assert 'multiple' in html
    assert 'name="uploads"' in html
    assert 'with-data' not in html
    assert 'name="uploads-0"' not in html

    html = field()
    assert 'with-data' in html
    assert 'name="uploads-0"' in html
    assert 'Uploaded file: baz.txt (3 Bytes) ✓' in html
    assert 'name="uploads-1"' in html
    assert 'Uploaded file: foobar.txt (6 Bytes) ✓' in html
    assert 'name="uploads-2"' not in html
    assert 'keep' in html
    assert 'type="file"' in html
    assert 'value="baz.txt"' not in html
    assert 'value="foobar.txt"' not in html
    assert 'Upload additional files' in html
    assert 'name="uploads"' in html
    assert 'without-data' in html
    assert 'multiple' in html

    html = field(resend_upload=True)
    assert 'with-data' in html
    assert 'Uploaded file: baz.txt (3 Bytes) ✓' in html
    assert 'Uploaded file: foobar.txt (6 Bytes) ✓' in html
    assert 'keep' in html
    assert 'type="file"' in html
    assert 'value="baz.txt"' in html
    assert 'value="foobar.txt"' in html

    # Test submit
    form, field = create_field()
    field.process(DummyPostData({}))
    assert field.validate(form)
    assert field.data == []

    form, field = create_field()
    field.process(DummyPostData({'uploads': 'abcd'}))
    assert field.validate(form)  # fails silently
    assert field.data == []

    # ... simple
    form, field = create_field()
    field.process(DummyPostData({'uploads': file2}))
    assert field.validate(form)
    assert len(field) == 1
    assert field[0].action == 'replace'
    assert field.data[0]['filename'] == 'foobar.txt'
    assert field.data[0]['mimetype'] == 'text/plain'
    assert field.data[0]['size'] == 6
    assert dictionary_to_binary(field.data[0]) == b'foobar'
    assert field[0].filename == 'foobar.txt'
    assert field[0].file.read() == b'foobar'

    # ... keep first file and upload a second
    previous = deepcopy(field.data)
    form, field = create_field()
    field.process(DummyPostData({
        'uploads': file1,
        'uploads-0': ['keep', file2]
    }), data=previous)
    assert field.validate(form)
    assert len(field) == 2
    assert field[0].action == 'keep'
    assert field[1].action == 'replace'
    assert field.data[1]['filename'] == 'baz.txt'
    assert field.data[1]['mimetype'] == 'text/plain'
    assert field.data[1]['size'] == 3
    assert dictionary_to_binary(field.data[1]) == b'baz'
    assert field[1].filename == 'baz.txt'
    assert field[1].file.read() == b'baz'

    # ... delete the first file and keep the second
    previous = deepcopy(field.data)
    form, field = create_field()
    field.process(DummyPostData({
        'uploads': '',
        'uploads-0': ['delete', file2],
        'uploads-1': ['keep', file1],
    }), data=previous)
    assert field.validate(form)
    assert len(field) == 2
    assert field[0].action == 'delete'
    assert field.data[0] == {}
    assert field[1].action == 'keep'

    # ... keep second file with keep upload instead of assuming
    # it will be passed backed in via data
    previous = deepcopy(field.data)
    form, field = create_field()
    field.process(DummyPostData({
        'uploads': '',
        # if we omit the first file from the post data the corresponding
        # field will disappear and become the new 0 index
        'uploads-1': [
            'keep', file1, previous[1]['filename'], previous[1]['data']
        ],
    }))
    assert field.validate(form)
    assert len(field) == 1
    assert field[0].action == 'keep'
    assert field[0].data['filename'] == 'baz.txt'
    assert field[0].data['mimetype'] == 'text/plain'
    assert field[0].data['size'] == 3
    assert dictionary_to_binary(field.data[0]) == b'baz'


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

    assert field.format == ['%Y-%m-%dT%H:%M']
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


def test_translated_select_field():

    form = Form()
    field = TranslatedSelectField()
    field = field.bind(form, 'choice')
    field.data = ''
    assert field()

    form = Form()
    field = TranslatedSelectField(choices=[])
    field = field.bind(form, 'choice')
    field.data = ''
    assert field()

    form = Form()
    field = TranslatedSelectField(choices=[('a', 'b')])
    field = field.bind(form, 'choice')
    field.data = ''
    field.meta.request = Bunch(translate=lambda x: 'xx')
    assert '<option value="a">xx</option>' in field()


def test_url_field():
    form = Form()
    field = URLField()
    field = field.bind(form, 'url')
    assert field.default_scheme == 'https'
    assert field.render_kw == {'placeholder': 'https://'}
    assert len(field.validators) == 1
    assert isinstance(field.validators[0], URL)
    assert field.validators[0].validate_hostname.require_tld is True
    assert field.validators[0].validate_hostname.allow_ip is False

    field.process_formdata([''])
    assert field.data == 'https://'
    assert not field.validate(form)

    field.process_formdata(['bogus'])
    assert field.data == 'https://bogus'
    assert not field.validate(form)

    field.process_formdata(['1.1.1.1'])
    assert field.data == 'https://1.1.1.1'
    assert not field.validate(form)

    field.process_formdata(['example.com'])
    assert field.data == 'https://example.com'
    assert field.validate(form)

    field.process_formdata(['http://example.com'])
    assert field.data == 'http://example.com'
    assert field.validate(form)

    form = Form()
    field = URLField(
        default_scheme=None,
        validators=[Optional(), URL(require_tld=False)]
    )
    field = field.bind(form, 'url')
    assert field.default_scheme is None
    assert field.render_kw is None
    assert len(field.validators) == 2
    assert isinstance(field.validators[1], URL)
    assert field.validators[1].validate_hostname.require_tld is False
    assert field.validators[1].validate_hostname.allow_ip is True

    # optional
    field.raw_data = ['']
    field.process_formdata([''])
    assert field.data == ''
    assert field.validate(form)

    # dummy raw_data so Optional doesn't trigger
    field.raw_data = ['set']
    field.process_formdata(['https://bogus'])
    assert field.data == 'https://bogus'
    assert field.validate(form)

    field.process_formdata(['https://1.1.1.1'])
    assert field.data == 'https://1.1.1.1'
    assert field.validate(form)

    field.process_formdata(['example.com'])
    assert field.data == 'example.com'
    assert not field.validate(form)

    field.process_formdata(['http://example.com'])
    assert field.data == 'http://example.com'
    assert field.validate(form)

    form = Form()
    field = URLField(render_kw={'size': 15, 'placeholder': '...'})
    field = field.bind(form, 'url')
    assert field.default_scheme == 'https'
    assert field.render_kw == {'size': 15, 'placeholder': '...'}
