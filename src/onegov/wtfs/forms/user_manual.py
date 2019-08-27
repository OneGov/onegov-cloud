from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.wtfs import _


class UserManualForm(Form):

    pdf = UploadField(
        label=_("PDF"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    def update_model(self, model):
        action = getattr(self.pdf, 'action', '')
        if action == 'delete':
            del model.pdf
        if action == 'replace':
            if self.pdf.data:
                model.pdf = self.pdf.raw_data[-1].file.read()

    def apply_model(self, model):
        if model.exists:
            self.pdf.data = {
                'filename': model.filename,
                'size': model.content_length,
                'mimetype': model.content_type
            }
