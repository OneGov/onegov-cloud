from cgi import FieldStorage
from datetime import date
from io import BytesIO
from onegov.core.utils import Bunch
from onegov.form import Form
from onegov.wtfs.fields import CsvUploadField
from onegov.wtfs.fields import HintField
from onegov.wtfs.fields import MunicipalityDataUploadField


class PostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_csv_field():
    form = Form()

    field = CsvUploadField()
    field = field.bind(form, 'upload')
    assert field()
    assert len(field.validators) == 2

    def process(content, **kwargs):
        field = CsvUploadField(**kwargs)
        field = field.bind(form, 'upload')

        field_storage = FieldStorage()
        field_storage.file = BytesIO(content)
        field_storage.type = 'text/plain'
        field_storage.filename = 'test.csv'

        field.process(PostData({'upload': field_storage}))
        return field

    # Invalid file
    field = process(b'a,b\n1')
    assert not field.validate(form)
    assert "Not a valid CSV file." in field.errors

    field = process(b'\xc3\x01')
    assert not field.validate(form)
    assert "Not a valid CSV file." in field.errors

    field = process(b'')
    assert not field.validate(form)
    assert "The file is empty." in field.errors

    field = process(b'a,b\n\n1,2')
    assert not field.validate(form)
    assert "The file contains an empty line." in field.errors

    # Invalid headers
    field = process(b'a,b,b\n1,2,2')
    assert not field.validate(form)
    assert "Some column names appear twice." in field.errors

    field = process(b'a,b,b\n1,2,2', rename_duplicate_column_names=True)
    assert field.validate(form)

    field = process(b'a,b\n1,2', expected_headers=['a', 'c'])
    assert not field.validate(form)
    assert "Some columns are missing." in field.errors

    # Valid
    field = process(b'a,b,c\n1,2,3\n4,5,6')
    assert field.validate(form)
    assert [(row.a, row.b, row.c) for row in field.data.lines] == [
        ('1', '2', '3'), ('4', '5', '6')
    ]


def test_municipality_data_upload_field():
    form = Form()

    def process(content, **kwargs):
        field = MunicipalityDataUploadField(**kwargs)
        field = field.bind(form, 'upload')

        field_storage = FieldStorage()
        field_storage.file = BytesIO(content)
        field_storage.type = 'text/plain'
        field_storage.filename = 'test.csv'

        field.process(PostData({'upload': field_storage}))
        return field

    # Invalid
    field = process(
        b'Gemeinde-Nr,Vordefinierte Termine\n'
        b'Adlikon,\n'
    )
    assert not field.validate(form)
    errors = [error.interpolate() for error in field.errors]
    assert "Some rows contain invalid values: 2." in errors

    field = process(
        b'Gemeinde-Nr,Vordefinierte Termine\n'
        b'21,Test\n'
    )
    assert not field.validate(form)
    errors = [error.interpolate() for error in field.errors]
    assert "Some rows contain invalid values: 2." in errors

    # Valid
    field = process(
        b'Gemeinde-Nr,Vordefinierte Termine\n'
        b'21,\n'
    )
    assert field.validate(form)
    assert field.data == {21: {'dates': []}}

    field = process(
        b'Gemeinde-Nr,Vordefinierte Termine,Vordefinierte Termine\n'
        b'21,01.01.2019,07.01.2019\n'
    )
    assert field.validate(form)
    assert field.data == {
        21: {'dates': [date(2019, 1, 1), date(2019, 1, 7)]}
    }


def test_hint_field(wtfs_app):
    def get_translate(for_chameleon):
        return wtfs_app.chameleon_translations.get('de_CH')

    form = Form()
    field = HintField(macro='express_shipment_hint')
    field = field.bind(form, 'hint')
    field.meta.request = Bunch(app=wtfs_app, get_translate=get_translate)

    assert field.validate(form)
    assert "Für dringende Scan-Aufträge" in field()
