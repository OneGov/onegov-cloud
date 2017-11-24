from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms import RadioField
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired


class UploadRestForm(Form):

    type = RadioField(
        _("Type"),
        choices=[
            ('vote', _("Vote")),
            ('election', _("Election")),
            ('parties', _("Party results")),
        ],
        validators=[
            InputRequired()
        ],
        default='vote'
    )

    id = StringField(
        label=_("Identifier"),
        validators=[
            InputRequired()
        ]
    )

    results = UploadField(
        label=_("Results"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )
