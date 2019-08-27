from cgi import FieldStorage
from datetime import date
from io import BytesIO
from onegov.core.utils import Bunch
from onegov.form import Form
from onegov.wtfs.fields import HintField
from onegov.wtfs.fields import MunicipalityDataUploadField


class PostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


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
    field = process('Bäretswil;\r\n'.encode('cp1252'))
    assert not field.validate(form)
    errors = [error.interpolate() for error in field.errors]
    assert "Some rows contain invalid values: 0." in errors

    # Valid
    field = process('Bäretswil;111;-1;Normal;\r\n'.encode('cp1252'))
    assert field.validate(form)
    assert field.data == {111: {'dates': []}}

    field = process(
        'Bäretswil;111;-1;Normal;01.01.2019;07.01.2019\r\n'.encode('cp1252')
    )
    assert field.validate(form)
    assert field.data == {
        111: {'dates': [date(2019, 1, 1), date(2019, 1, 7)]}
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
