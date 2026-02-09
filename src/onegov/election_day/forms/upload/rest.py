from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES_XML
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import InputRequiredIf
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired


class UploadRestForm(Form):

    type = RadioField(
        _('Type'),
        choices=[
            ('vote', _('Vote')),
            ('election', _('Election')),
            ('parties', _('Party results')),
            ('xml', 'eCH-0252'),
        ],
        validators=[
            InputRequired()
        ],
        default='vote'
    )

    id = StringField(
        label=_('Identifier'),
        validators=[
            InputRequiredIf('type', '!xml')
        ]
    )

    results = UploadField(
        label=_('Results'),
        validators=[
            DataRequired(),
            FileSizeLimit(50 * 1024 * 1024)
        ],
        allowed_mimetypes=(
            ALLOWED_MIME_TYPES | ALLOWED_MIME_TYPES_XML,
        ),
        render_kw={'force_simple': True}
    )
