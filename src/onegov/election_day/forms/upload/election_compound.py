from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms.fields import RadioField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired


class UploadElectionCompoundForm(Form):

    file_format = RadioField(
        _('File format'),
        choices=[
            ('internal', _('OneGov Cloud')),
        ],
        validators=[
            InputRequired()
        ],
        default='internal'
    )

    results = UploadField(
        label=_('Results'),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
    )
