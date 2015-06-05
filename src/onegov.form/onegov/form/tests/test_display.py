# -*- coding: utf-8 -*-
from datetime import datetime, time
from onegov.form import render_field


class MockField(object):

    def __init__(self, type, data):
        self.type = type
        self.data = data


def test_render_textfields():
    assert render_field(MockField('StringField', 'asdf')) == 'asdf'
    assert render_field(MockField('StringField', '<b>')) == '&lt;b&gt;'


def test_render_password():
    assert render_field(MockField('PasswordField', '123')) == '***'
    assert render_field(MockField('PasswordField', '1234')) == '****'
    assert render_field(MockField('PasswordField', '12345')) == '*****'


def test_render_date_field():
    assert render_field(MockField('DateField', datetime(1984, 4, 6)))\
        == '06.04.1984'
    assert render_field(MockField('DateTimeLocalField', datetime(1984, 4, 6)))\
        == '06.04.1984 00:00'
    assert render_field(MockField('TimeField', time(10, 0))) == '10:00'


def test_render_upload_field():
    assert render_field(MockField('UploadField', {
        'filename': '<b.txt>', 'size': 1000
    })) == '&lt;b.txt&gt; (1.0 kB)'


def test_render_radio_field():
    assert render_field(MockField('RadioField', 'selected')) == u'✓ selected'


def test_render_multi_checkbox_field():
    assert render_field(MockField('MultiCheckboxField', ['a', 'b']))\
        == u'✓ a<br>✓ b'
