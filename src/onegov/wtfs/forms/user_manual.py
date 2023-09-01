from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.wtfs import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.wtfs.models import UserManual


class UserManualForm(Form):

    pdf = UploadField(
        label=_("PDF"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    def update_model(self, model: 'UserManual') -> None:
        action = getattr(self.pdf, 'action', '')
        if action == 'delete':
            del model.pdf
        if action == 'replace':
            if self.pdf.data:
                model.pdf = self.pdf.file.read()  # type:ignore

    def apply_model(self, model: 'UserManual') -> None:
        if model.exists:
            content_length = model.content_length
            assert content_length is not None
            self.pdf.data = {
                'filename': model.filename,
                'size': content_length,
                'mimetype': model.content_type
            }
