from cgi import FieldStorage
from io import BytesIO


from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import WhitelistedMimeType
from onegov.gis import CoordinatesField
from onegov.translator_directory import _

ALLOWED_MIME_TYPES = {
    'application/excel',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-office',
}


class TranslatorDirectorySettingsForm(Form):

    coordinates = CoordinatesField(
        fieldset=_("Home Location"),
        render_kw={'data-map-type': 'marker', 'data-undraggable': 1},
    )

    voucher_excel = UploadField(
        label=_('Voucher template'),
        fieldset=_("Templates"),
        validators=[WhitelistedMimeType(ALLOWED_MIME_TYPES)]
    )

    def update_model(self, app):
        if self.coordinates.data:
            app.coordinates = self.coordinates.data

        if self.voucher_excel.action == 'delete':
            self.request.session.delete(app.voucher_excel)
            self.request.session.flush()
        if self.voucher_excel.action == 'replace':
            if self.voucher_excel.data:
                app.voucher_excel_file = self.voucher_excel.raw_data[-1].file

    def apply_model(self, app):
        self.coordinates.data = app.coordinates
        if app.voucher_excel:
            fs = FieldStorage()
            fs.file = BytesIO(app.voucher_excel_file.read())
            fs.type = app.voucher_excel_file.content_type
            fs.filename = app.voucher_excel_file.filename
            self.voucher_excel.data = self.voucher_excel.\
                process_fieldstorage(fs)
