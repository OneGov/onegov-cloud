from __future__ import annotations
from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES_XML
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from wtforms.validators import DataRequired


class UploadEchForm(Form):

    xml = UploadField(
        label=_('Delivery'),
        validators=[
            DataRequired(),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        allowed_mimetypes=ALLOWED_MIME_TYPES_XML,
        render_kw={'force_simple': True}
    )
